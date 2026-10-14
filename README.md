# QuizIn

QuizIn can be played in the browser or from the existing terminal interface.

## Browser app

From the project folder, run:

```powershell
python web_app.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000). The browser app uses only Python's standard library and serves the quiz locally. Press `Ctrl+C` in the terminal to stop it.

The browser UI includes topic selection, a 15-second countdown per question, quiz results, answer review, and the existing saved leaderboard. Use the **Review my answers** button after a quiz to see your responses and correct answers.

## Terminal app

The original terminal app remains available:

```powershell
python main.py
```
