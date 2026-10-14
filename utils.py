import math
import time


def get_non_empty_input(prompt):
    """Keep asking until the user enters non-empty text."""
    while True:
        value = input(prompt).strip()
 
        if value:
            return value
 
        print("Input cannot be empty. Please try again.")
 
 
def get_menu_choice(prompt, valid_choices):
    """Accept only one of the allowed choices."""
    while True:
        choice = input(prompt).strip()
 
        if choice in valid_choices:
            return choice
 
        print(
            "Invalid choice. Please enter one of:",
            ", ".join(valid_choices)
        )


def get_timed_menu_choice(prompt, valid_choices, timeout_seconds=15):
    """Read a menu choice until a valid choice is entered or time expires."""
    import msvcrt

    deadline = time.monotonic() + timeout_seconds
    choice = ""
    displayed_length = 0
    displayed_seconds = None

    def show_status(remaining_seconds):
        nonlocal displayed_length
        status = (
            f"{prompt}{choice}"
            f"  Time remaining: {remaining_seconds}s"
        )
        print(
            "\r" + status + " " * max(0, displayed_length - len(status)),
            end="",
            flush=True
        )
        displayed_length = len(status)

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        remaining_seconds = math.ceil(remaining)
        if remaining_seconds != displayed_seconds:
            show_status(remaining_seconds)
            displayed_seconds = remaining_seconds

        if not msvcrt.kbhit():
            time.sleep(min(0.05, remaining))
            continue

        character = msvcrt.getwch()

        if character in ("\x00", "\xe0"):
            if msvcrt.kbhit():
                msvcrt.getwch()
            continue

        if character == "\x03":
            raise KeyboardInterrupt

        if character in ("\r", "\n"):
            if choice in valid_choices:
                print()
                return choice

            print()
            print(
                "Invalid choice. Please enter one of:",
                ", ".join(valid_choices)
            )
            choice = ""
            displayed_length = 0
            displayed_seconds = None
            continue

        if character == "\b":
            if choice:
                choice = choice[:-1]
                show_status(remaining_seconds)
            continue

        if character.isprintable():
            choice += character
            show_status(remaining_seconds)

    print()
    print("\nTime's up!")
    return None
 