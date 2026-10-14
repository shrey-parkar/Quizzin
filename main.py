from questions import QUESTIONS
from quiz_engine import run_quiz, display_quiz_review
from leaderboard import load_leaderboard, add_result, display_leaderboard
from utils import get_non_empty_input, get_menu_choice
 
 
TOPICS = [
    "Python",
    "Science",
    "General Knowledge",
    "All Topics"
]
 
 
def show_menu():
    print("\n" + "=" * 40)
    print("         QUIZ GAME")
    print("=" * 40)
    print("1. Play Quiz")
    print("2. View Leaderboard")
    print("3. Exit")
    print("=" * 40)
 
 
def choose_topic():
    print("\nChoose a topic:")
 
    for index, topic in enumerate(TOPICS, start=1):
        print(f"{index}. {topic}")
 
    choice = get_menu_choice(
        "Enter your choice (1-4): ",
        ["1", "2", "3", "4"]
    )
 
    return TOPICS[int(choice) - 1]
 
 
def main():
    leaderboard = load_leaderboard()
 
    print("\nWelcome to the Quiz Game!")
 
    while True:
        show_menu()
 
        choice = get_menu_choice(
            "Enter your choice (1-3): ",
            ["1", "2", "3"]
        )
 
        if choice == "1":
            player_name = get_non_empty_input(
                "\nEnter your name: "
            )
 
            topic = choose_topic()
            result = run_quiz(player_name, topic, QUESTIONS)

            if result is not None:
                quiz_review = result["responses"]
                leaderboard_result = {
                    key: value
                    for key, value in result.items()
                    if key != "responses"
                }
                leaderboard = add_result(leaderboard, leaderboard_result)
                display_leaderboard(leaderboard)
 
                print("\n1. Play Again")
                print("2. Main Menu")
                print("3. Exit")
                print("4. Review Attempted Quiz")
 
                next_action = get_menu_choice(
                    "Choose an option (1-4): ",
                    ["1", "2", "3", "4"]
                )
 
                if next_action == "1":
                    continue
                elif next_action == "3":
                    print("Thanks for playing. Goodbye!")
                    break
                elif next_action == "4":
                    display_quiz_review(quiz_review)
 
        elif choice == "2":
            display_leaderboard(leaderboard)
 
        elif choice == "3":
            print("Thanks for playing. Goodbye!")
            break
 
 
if __name__ == "__main__":
    main()