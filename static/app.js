const app = document.querySelector("#app");
const toast = document.querySelector("#toast");
const homeNav = document.querySelector("#home-nav");
const leaderboardNav = document.querySelector("#leaderboard-nav");
let countdownId = null;
let toastTimeout = null;

function escapeText(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("visible");
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => toast.classList.remove("visible"), 3500);
}

async function request(path, data) {
    const options = { headers: {} };
    if (data !== undefined) {
        options.method = "POST";
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(data);
    }
    const response = await fetch(path, options);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Something went wrong.");
    return payload;
}

function setActiveNav(section) {
    homeNav.classList.toggle("active", section === "home");
    leaderboardNav.classList.toggle("active", section === "leaderboard");
}

function stopCountdown() {
    if (countdownId !== null) {
        clearInterval(countdownId);
        countdownId = null;
    }
}

async function showHome() {
    stopCountdown();
    setActiveNav("home");
    app.innerHTML = '<div class="loading">Loading topics…</div>';
    try {
        const { topics } = await request("/api/topics");
        app.innerHTML = `
            <section class="hero">
                <span class="eyebrow">A little challenge, a lot of fun</span>
                <h1>Ready to test<br>what you know?</h1>
                <p>Pick a topic, trust your instincts, and see how far your curiosity takes you.</p>
            </section>
            <section class="home-grid">
                <form class="card setup-card" id="start-form">
                    <div class="card-heading">
                        <h2>Your next quiz starts here</h2>
                        <p>Ten questions. Fifteen seconds each. You’ve got this.</p>
                    </div>
                    <label class="field">
                        <span class="field-label">Your name</span>
                        <input class="text-input" name="player" maxlength="40" autocomplete="name" placeholder="e.g. Alex Morgan" required>
                    </label>
                    <label class="field">
                        <span class="field-label">Choose a topic</span>
                        <select class="select-input" name="topic">
                            ${topics.map(topic => `<option value="${escapeText(topic)}">${escapeText(topic)}</option>`).join("")}
                        </select>
                    </label>
                    <button class="primary-button wide" type="submit">Start my quiz <span aria-hidden="true">→</span></button>
                    <div class="setup-note"><span class="note-icon" aria-hidden="true">✦</span><span><strong>No pressure.</strong> Your answers stay private until you finish. Review every question at the end.</span></div>
                </form>
                <aside class="card side-card">
                    <div class="side-top">
                        <span class="side-label">The QuizIn experience</span>
                        <h2>Make every minute a little smarter.</h2>
                        <p>Short, focused quizzes designed to keep learning light and rewarding.</p>
                        <ul class="feature-list">
                            <li><span class="feature-check">✓</span> A fresh set of questions every time</li>
                            <li><span class="feature-check">✓</span> A fair timer for every answer</li>
                            <li><span class="feature-check">✓</span> Your answers, explained at the end</li>
                        </ul>
                    </div>
                    <div class="side-art" aria-hidden="true"><span class="art-tile">✎</span><span class="art-tile">✦</span><span class="art-tile">◎</span></div>
                </aside>
            </section>`;
        document.querySelector("#start-form").addEventListener("submit", startQuiz);
    } catch (error) {
        showToast(error.message, true);
    }
}

async function startQuiz(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type=submit]");
    const formData = new FormData(form);
    button.disabled = true;
    button.textContent = "Preparing your quiz…";
    try {
        const question = await request("/api/start", {
            player: formData.get("player"),
            topic: formData.get("topic")
        });
        renderQuestion(question);
    } catch (error) {
        showToast(error.message, true);
        button.disabled = false;
        button.innerHTML = 'Start my quiz <span aria-hidden="true">→</span>';
    }
}

function renderQuestion(data) {
    stopCountdown();
    setActiveNav("");
    const percentage = ((data.number - 1) / data.total) * 100;
    app.innerHTML = `
        <section class="card quiz-card">
            <div class="quiz-meta">
                <span class="topic-pill"><span aria-hidden="true">✦</span> ${escapeText(data.topic)}</span>
                <span class="question-count">Question ${data.number} of ${data.total}</span>
            </div>
            <div class="progress-track" role="progressbar" aria-label="Quiz progress" aria-valuemin="0" aria-valuemax="${data.total}" aria-valuenow="${data.number - 1}">
                <div class="progress-fill" style="width:${percentage}%"></div>
            </div>
            <div class="timer-row"><span class="timer-label">Choose your answer</span><span class="timer-value" id="timer-value" aria-live="off">${data.time_limit}s</span></div>
            <h1 class="quiz-question">${escapeText(data.question)}</h1>
            <div class="options" role="group" aria-label="Answer choices">
                ${data.options.map((option, index) => `
                    <button class="option-button" type="button" data-choice="${index}">
                        <span class="option-key">${String.fromCharCode(65 + index)}</span>
                        <span class="option-copy">${escapeText(option)}</span>
                    </button>`).join("")}
            </div>
            <div class="quiz-foot"><span>Answer before the timer runs out</span><span><strong>${escapeText(data.player)}</strong> · ${data.total} questions</span></div>
        </section>`;
    document.querySelectorAll(".option-button").forEach(button => {
        button.addEventListener("click", () => submitAnswer(Number(button.dataset.choice)));
    });
    startCountdown(data.time_limit);
}

function startCountdown(seconds) {
    let remaining = seconds;
    const timer = document.querySelector("#timer-value");
    countdownId = setInterval(() => {
        remaining -= 1;
        if (!timer) return stopCountdown();
        timer.textContent = `${Math.max(remaining, 0)}s`;
        timer.classList.toggle("urgent", remaining <= 5);
        if (remaining <= 0) {
            stopCountdown();
            submitAnswer(null);
        }
    }, 1000);
}

async function submitAnswer(choice) {
    stopCountdown();
    document.querySelectorAll(".option-button").forEach(button => {
        button.disabled = true;
    });
    try {
        const response = await request("/api/answer", { choice });
        if (response.state === "results") renderResults(response.result);
        else renderQuestion(response);
    } catch (error) {
        showToast(error.message, true);
        showHome();
    }
}

function renderResults(result) {
    stopCountdown();
    lastResult = result;
    setActiveNav("");
    app.innerHTML = `
        <section class="card result-card">
            <div class="result-medal" aria-hidden="true">✦</div>
            <span class="eyebrow">Quiz complete</span>
            <h1>Well done, ${escapeText(result.player)}!</h1>
            <p class="result-subtitle">${escapeText(result.grade)} You’ve finished your ${escapeText(result.topic)} quiz.</p>
            <div class="score-panel">
                <div class="score-item"><span class="score-value">${result.score}/${result.total}</span><span class="score-label">Score</span></div>
                <div class="score-item"><span class="score-value">${Number(result.percentage).toFixed(1)}%</span><span class="score-label">Accuracy</span></div>
                <div class="score-item"><span class="score-value">${escapeText(result.grade)}</span><span class="score-label">Feedback</span></div>
            </div>
            <div class="result-actions">
                <button class="primary-button" id="review-button">Review my answers</button>
                <button class="secondary-button" id="again-button">Play again</button>
                <button class="secondary-button" id="results-board-button">Leaderboard</button>
            </div>
        </section>`;
    document.querySelector("#review-button").addEventListener("click", showReview);
    document.querySelector("#again-button").addEventListener("click", showHome);
    document.querySelector("#results-board-button").addEventListener("click", showLeaderboard);
}

async function showReview() {
    try {
        const { responses } = await request("/api/review", {});
        setActiveNav("");
        app.innerHTML = `
            <section class="review-wrap">
                <div class="review-heading">
                    <div><span class="eyebrow">Answer breakdown</span><h1>Your quiz review</h1><p>See what you chose and learn from every question.</p></div>
                    <div class="inline-actions"><button class="secondary-button" id="review-back">Back to results</button><button class="primary-button" id="review-home">New quiz</button></div>
                </div>
                <div class="review-list">
                    ${responses.map((item, index) => {
                        const correct = item.your_answer === item.correct_answer;
                        const status = item.your_answer === "No answer" ? "Not answered" : correct ? "Correct" : "Incorrect";
                        return `<article class="review-item">
                            <span class="review-number">${String(index + 1).padStart(2, "0")}</span>
                            <div>
                                <div class="review-topic">${escapeText(item.topic)} · ${status}</div>
                                <p class="review-question">${escapeText(item.question)}</p>
                                ${correct
                                    ? `<div class="review-answer correct"><strong>Your answer:</strong> ${escapeText(item.your_answer)} <span aria-label="Correct">✓</span></div>`
                                    : `<div class="review-answer incorrect"><strong>Your answer:</strong> ${escapeText(item.your_answer)}</div><div class="review-answer"><strong>Correct answer:</strong> ${escapeText(item.correct_answer)}</div>`}
                            </div>
                        </article>`;
                    }).join("")}
                </div>
            </section>`;
        document.querySelector("#review-back").addEventListener("click", () => {
            showResultsAgain();
        });
        document.querySelector("#review-home").addEventListener("click", showHome);
    } catch (error) {
        showToast(error.message, true);
    }
}

let lastResult = null;
function showResultsAgain() {
    if (lastResult) renderResults(lastResult);
    else showHome();
}

async function showLeaderboard() {
    stopCountdown();
    setActiveNav("leaderboard");
    app.innerHTML = '<div class="loading">Loading leaderboard…</div>';
    try {
        const { results } = await request("/api/leaderboard");
        app.innerHTML = `
            <section class="card leaderboard-card">
                <div class="leaderboard-title">
                    <div><span class="eyebrow">Top scores</span><h1>Leaderboard</h1></div>
                    <button class="primary-button" id="leaderboard-play">Play a quiz</button>
                </div>
                ${results.length ? `
                    <div class="table-scroll"><table class="leaderboard-table">
                        <thead><tr><th>Rank</th><th>Player</th><th>Topic</th><th>Score</th><th>Accuracy</th></tr></thead>
                        <tbody>${results.map((item, index) => `<tr>
                            <td class="rank">${String(index + 1).padStart(2, "0")}</td>
                            <td><strong>${escapeText(item.player)}</strong></td>
                            <td>${escapeText(item.topic)}</td>
                            <td><span class="score-chip">${item.score}/${item.total}</span></td>
                            <td>${Number(item.percentage).toFixed(1)}%</td>
                        </tr>`).join("")}</tbody>
                    </table></div>` : `<div class="empty-state"><div class="empty-icon">✦</div><strong>No scores yet</strong><p>Play your first quiz and claim the top spot.</p></div>`}
            </section>`;
        document.querySelector("#leaderboard-play").addEventListener("click", showHome);
    } catch (error) {
        showToast(error.message, true);
    }
}

homeNav.addEventListener("click", showHome);
leaderboardNav.addEventListener("click", showLeaderboard);
document.addEventListener("keydown", event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const optionButtons = document.querySelectorAll(".option-button:not(:disabled)");
    const key = event.key.toLowerCase();
    if (!/^[a-d]$/.test(key)) return;
    const selectedKey = key.charCodeAt(0) - 97;
    if (selectedKey >= 0 && selectedKey < optionButtons.length) {
        optionButtons[selectedKey].click();
    }
});

showHome();
