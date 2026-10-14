import json
from pathlib import Path
 
 
LEADERBOARD_FILE = Path(__file__).with_name("leaderboard.json")
 
 
def load_leaderboard():
    """Load saved results. Return an empty list if none exist."""
    if not LEADERBOARD_FILE.exists():
        return []
 
    try:
        with LEADERBOARD_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
 
        if isinstance(data, list):
            return [
                entry for entry in data
                if isinstance(entry, dict)
                and isinstance(entry.get("score"), int)
                and isinstance(entry.get("player"), str)
            ]
 
        print("Leaderboard data is invalid. Starting with an empty list.")
        return []
 
    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not read leaderboard: {error}")
        return []
 
 
def save_leaderboard(results):
    """Write all results to the JSON file."""
    try:
        with LEADERBOARD_FILE.open("w", encoding="utf-8") as file:
            json.dump(results, file, indent=4, ensure_ascii=False)
        return True
 
    except OSError as error:
        print(f"Could not save leaderboard: {error}")
        return False
 
 
def add_result(results, result):
    """Add a completed quiz and sort best results first."""
    updated_results = results.copy()
    updated_results.append(result)
 
    updated_results.sort(
        key=lambda item: (
            item["score"],
            item["percentage"]
        ),
        reverse=True
    )
 
    if save_leaderboard(updated_results):
        return updated_results
 
    # Keep the current session usable if saving fails.
    print("Result retained for this session only.")
    return updated_results
 
 
def display_leaderboard(results):
    """Display the five highest-scoring results."""
    print("\n" + "=" * 65)
    print("TOP 5 LEADERBOARD")
    print("=" * 65)
 
    if not results:
        print("No results yet. Play a quiz to appear here.")
        print("=" * 65)
        return
 
    print(
        f"{'Rank':<6}{'Player':<20}"
        f"{'Topic':<23}{'Score':<9}{'Percent':<8}"
    )
    print("-" * 65)
 
    for rank, result in enumerate(results[:5], start=1):
        print(
            f"{rank:<6}"
            f"{result['player'][:19]:<20}"
            f"{result['topic'][:22]:<23}"
            f"{result['score']}/{result['total']:<7}"
            f"{result['percentage']:.1f}%"
        )
 
    print("=" * 65 )