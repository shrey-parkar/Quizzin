import random
from utils import get_timed_menu_choice
 
 
QUESTIONS_PER_QUIZ = 10
QUESTION_TIME_LIMIT_SECONDS = 15
 
 
def get_questions_for_topic(question_bank, topic):
    """Return questions matching the selected topic."""
    if topic == "All Topics":
        return question_bank.copy()
 
    return [
        question for question in question_bank
        if question["topic"] == topic
    ]
 
 
def get_grade(percentage):
    """Return feedback based on the percentage."""
    if percentage >= 90:
        return "Excellent!"
    elif percentage >= 70:
        return "Great job!"
    elif percentage >= 50:
        return "Good effort!"
    else:
        return "Keep practicing!"


def display_quiz_review(responses):
    """Display each attempted question with the chosen and correct answers."""
    print("\n" + "=" * 45)
    print("QUIZ REVIEW")
    print("=" * 45)

    for number, response in enumerate(responses, start=1):
        print(f"\nQuestion {number}: [{response['topic']}] {response['question']}")

        if response["your_answer"] == response["correct_answer"]:
            print(f"Your answer: {response['your_answer']} (Correct)")
        else:
            print(f"Your answer: {response['your_answer']}")
            print(f"Correct answer: {response['correct_answer']}")


def run_quiz(player_name, topic, question_bank):
    """Run one quiz and return its result as a dictionary."""
    available_questions = get_questions_for_topic(
        question_bank, topic
    )
 
    if len(available_questions) < QUESTIONS_PER_QUIZ:
        print("Not enough questions available for this topic.")
        return None
 
    selected_questions = random.sample(
        available_questions, QUESTIONS_PER_QUIZ
    )
 
    score = 0
    responses = []
 
    print("\n" + "=" * 45)
    print(f"Player: {player_name}")
    print(f"Topic: {topic}")
    print(f"Number of questions: {QUESTIONS_PER_QUIZ}")
    print("=" * 45)
 
    for number, question in enumerate(selected_questions, start=1):
        print(f"\nQuestion {number}/{QUESTIONS_PER_QUIZ}")
        print(f"[{question['topic']}] {question['question']}")
 
        for index, option in enumerate(question["options"], start=1):
            print(f"{index}. {option}")
 
        valid_choices = ["1", "2", "3", "4"]
        answer = get_timed_menu_choice(
            (
                "Your answer (1-4; "
                f"{QUESTION_TIME_LIMIT_SECONDS} seconds): "
            ),
            valid_choices,
            QUESTION_TIME_LIMIT_SECONDS
        )

        correct_index = question["answer"]
        your_answer = (
            question["options"][int(answer) - 1]
            if answer is not None
            else "No answer"
        )
        correct_answer = question["options"][correct_index]

        if answer is not None:
            if int(answer) - 1 == correct_index:
                score += 1
                print("Correct! Well done.")
            else:
                print("Incorrect.")

        responses.append({
            "topic": question["topic"],
            "question": question["question"],
            "your_answer": your_answer,
            "correct_answer": correct_answer
        })
 
    percentage = (score / QUESTIONS_PER_QUIZ) * 100
    grade = get_grade(percentage)
 
    print("\n" + "=" * 45)
    print("QUIZ RESULTS")
    print("=" * 45)
    print(f"Player: {player_name}")
    print(f"Score: {score}/{QUESTIONS_PER_QUIZ}")
    print(f"Percentage: {percentage:.1f}%")
    print(f"Feedback: {grade}")
    print("=" * 45)
 
    return {
        "player": player_name,
        "topic": topic,
        "score": score,
        "total": QUESTIONS_PER_QUIZ,
        "percentage": round(percentage, 1),
        "grade": grade,
        "responses": responses
    }
