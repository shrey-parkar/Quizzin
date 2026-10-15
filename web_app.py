import json
import random
import secrets
import threading
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from leaderboard import add_result, load_leaderboard
from questions import QUESTIONS
from quiz_engine import (
    QUESTIONS_PER_QUIZ,
    QUESTION_TIME_LIMIT_SECONDS,
    get_grade,
    get_questions_for_topic,
)


HOST = "127.0.0.1"
PORT = 8000
ROOT = Path(__file__).parent
SESSIONS = {}
SESSIONS_LOCK = threading.Lock()


class QuizRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self._send_file(ROOT / "templates" / "index.html", "text/html")
        elif path == "/static/styles.css":
            self._send_file(ROOT / "static" / "styles.css", "text/css")
        elif path == "/static/app.js":
            self._send_file(
                ROOT / "static" / "app.js",
                "text/javascript; charset=utf-8"
            )
        elif path == "/api/topics":
            topics = list(dict.fromkeys(question["topic"] for question in QUESTIONS))
            self._send_json({"topics": topics + ["All Topics"]})
        elif path == "/api/leaderboard":
            self._send_json({"results": load_leaderboard()[:5]})
        else:
            self._send_json({"error": "Page not found."}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self._read_json()
            if path == "/api/start":
                self._start_quiz(data)
            elif path == "/api/answer":
                self._answer_question(data)
            elif path == "/api/review":
                self._send_review()
            else:
                self._send_json(
                    {"error": "Page not found."},
                    HTTPStatus.NOT_FOUND
                )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json(
                {"error": str(error) or "Invalid request."},
                HTTPStatus.BAD_REQUEST
            )

    def _read_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid request length.") from error

        if content_length < 0 or content_length > 16_384:
            raise ValueError("Request body is too large.")

        raw_body = self.rfile.read(content_length)
        data = json.loads(raw_body.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    def _start_quiz(self, data):
        player = data.get("player")
        topic = data.get("topic")
        available_topics = {
            question["topic"] for question in QUESTIONS
        } | {"All Topics"}

        if not isinstance(player, str) or not player.strip():
            raise ValueError("Please enter your name.")
        if len(player.strip()) > 40:
            raise ValueError("Name must be 40 characters or fewer.")
        if not isinstance(topic, str) or topic not in available_topics:
            raise ValueError("Choose a valid quiz topic.")

        available_questions = get_questions_for_topic(QUESTIONS, topic)
        if len(available_questions) < QUESTIONS_PER_QUIZ:
            raise ValueError("There are not enough questions for this topic.")

        quiz_session = {
            "player": player.strip(),
            "topic": topic,
            "questions": random.sample(
                available_questions,
                QUESTIONS_PER_QUIZ
            ),
            "responses": [],
            "score": 0,
            "question_index": 0,
            "deadline": time.monotonic() + QUESTION_TIME_LIMIT_SECONDS,
            "completed": False,
            "lock": threading.Lock(),
        }

        session_id = secrets.token_urlsafe(24)
        with SESSIONS_LOCK:
            SESSIONS[session_id] = quiz_session

        self._send_json(
            self._question_payload(quiz_session),
            headers={"Set-Cookie": f"quiz_session={session_id}; HttpOnly; SameSite=Lax; Path=/"}
        )

    def _get_session(self):
        cookies = SimpleCookie()
        cookies.load(self.headers.get("Cookie", ""))
        session_cookie = cookies.get("quiz_session")
        if session_cookie is None:
            return None
        with SESSIONS_LOCK:
            return SESSIONS.get(session_cookie.value)

    def _question_payload(self, quiz_session):
        question = quiz_session["questions"][quiz_session["question_index"]]
        return {
            "state": "question",
            "player": quiz_session["player"],
            "topic": quiz_session["topic"],
            "number": quiz_session["question_index"] + 1,
            "total": QUESTIONS_PER_QUIZ,
            "time_limit": QUESTION_TIME_LIMIT_SECONDS,
            "question": question["question"],
            "options": question["options"],
        }

    def _answer_question(self, data):
        quiz_session = self._get_session()
        if quiz_session is None:
            self._send_json(
                {"error": "Your quiz session expired. Please start again."},
                HTTPStatus.CONFLICT
            )
            return
        with quiz_session["lock"]:
            if quiz_session["completed"]:
                self._send_json(
                    {"error": "This quiz has already been completed."},
                    HTTPStatus.CONFLICT
                )
                return

            question = quiz_session["questions"][quiz_session["question_index"]]
            choice = data.get("choice")
            if choice is not None and (
                not isinstance(choice, int)
                or isinstance(choice, bool)
                or choice < 0
                or choice >= len(question["options"])
            ):
                raise ValueError("Choose one of the listed answers.")

            timed_out = time.monotonic() >= quiz_session["deadline"]
            selected_answer = (
                question["options"][choice]
                if choice is not None and not timed_out
                else "No answer"
            )
            correct_answer = question["options"][question["answer"]]
            is_correct = selected_answer == correct_answer
            quiz_session["responses"].append({
                "topic": question["topic"],
                "question": question["question"],
                "your_answer": selected_answer,
                "correct_answer": correct_answer,
            })
            if is_correct:
                quiz_session["score"] += 1

            quiz_session["question_index"] += 1
            if quiz_session["question_index"] == QUESTIONS_PER_QUIZ:
                quiz_session["completed"] = True
                self._finish_quiz(quiz_session)
                return

            quiz_session["deadline"] = time.monotonic() + QUESTION_TIME_LIMIT_SECONDS
            self._send_json(self._question_payload(quiz_session))

    def _finish_quiz(self, quiz_session):
        percentage = (
            quiz_session["score"] / QUESTIONS_PER_QUIZ
        ) * 100
        result = {
            "player": quiz_session["player"],
            "topic": quiz_session["topic"],
            "score": quiz_session["score"],
            "total": QUESTIONS_PER_QUIZ,
            "percentage": round(percentage, 1),
            "grade": get_grade(percentage),
        }
        add_result(load_leaderboard(), result)
        self._send_json({"state": "results", "result": result})

    def _send_review(self):
        quiz_session = self._get_session()
        if quiz_session is None or not quiz_session["completed"]:
            self._send_json(
                {"error": "Complete a quiz before opening its review."},
                HTTPStatus.CONFLICT
            )
            return
        with quiz_session["lock"]:
            self._send_json({"responses": quiz_session["responses"]})

    def _send_file(self, path, content_type):
        try:
            body = path.read_bytes()
        except OSError:
            self._send_json(
                {"error": "The requested UI resource could not be loaded."},
                HTTPStatus.INTERNAL_SERVER_ERROR
            )
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data, status=HTTPStatus.OK, headers=None):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), QuizRequestHandler)
    print(f"Quiz app is running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the quiz app.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
