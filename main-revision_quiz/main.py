import json
import os
import sys

# -------------------------------
# Constants
# -------------------------------
QUESTIONS_DIR = "questions"
PERFORMANCE_FILE = "performance.json"

LEVELS = ["GCSE", "ALevel"]
SUBJECTS = [
    "Maths",
    "Further_Maths",
    "Physics",
    "Biology",
    "Chemistry",
    "Computer_Science",
]


# -------------------------------
# Helper Functions
# -------------------------------
def clear_screen():
    """Clear the terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


# -------------------------------
# File Handling
# -------------------------------
def load_questions(level, subject):
    filename = f"{level}_{subject}.json"
    path = os.path.join(QUESTIONS_DIR, filename)
    if not os.path.exists(path):
        print(f"Error: {filename} not found in {QUESTIONS_DIR}")
        return []
    with open(path, "r") as file:
        return json.load(file)


def load_performance():
    if not os.path.exists(PERFORMANCE_FILE):
        return {}
    try:
        with open(PERFORMANCE_FILE, "r") as file:
            content = file.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        print("Warning: performance.json is corrupted. Starting fresh.\n")
        return {}


def save_performance(performance):
    with open(PERFORMANCE_FILE, "w") as file:
        json.dump(performance, file, indent=4)


# -------------------------------
# Utility Functions
# -------------------------------
def choose_option(options, prompt, allow_back=False):
    """Show a numbered menu and return the selected option."""
    while True:
        print("\n" + prompt)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option.replace('_', ' ')}")
        extra = 0
        if allow_back:
            extra = 1
            print(f"{len(options) + 1}. Go back")
        print(f"{len(options) + 1 + extra}. Exit")

        choice = input("Enter number: ").strip()
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            elif allow_back and choice == len(options) + 1:
                return "BACK"
            elif choice == len(options) + 1 + extra:
                print("Exiting program. Goodbye!")
                sys.exit()
        print("Invalid input. Please try again.")


def get_accuracy(data):
    if data["attempted"] == 0:
        return 0
    return data["correct"] / data["attempted"]


# -------------------------------
# Quiz Logic
# -------------------------------
def ask_question(question, performance, key):
    topic = question["topic"]
    correct_answer = question["answer"]

    # support multiple keyword answers
    if isinstance(correct_answer, list):
        correct_answer = [a.lower().strip() for a in correct_answer]
    else:
        correct_answer = [correct_answer.lower().strip()]

    user_answer = input("\n" + question["question"] + " ").lower().strip()

    if topic not in performance[key]:
        performance[key][topic] = {"attempted": 0, "correct": 0}

    performance[key][topic]["attempted"] += 1

    if any(ans in user_answer for ans in correct_answer):
        print("✅ Correct!\n")
        performance[key][topic]["correct"] += 1
    else:
        print(f"❌ Incorrect. Correct answer: {', '.join(correct_answer)}\n")


# -------------------------------
# Performance Viewing
# -------------------------------
def view_performance(performance):
    clear_screen()
    if not performance:
        print("\nNo performance data found.\n")
        input("Press Enter to return to main menu...")
        return

    print("\nAll Recorded Performance:\n------------------------")
    for key, topics in performance.items():
        print(f"\n{key.replace('_', ' ')}:")
        for topic, stats in topics.items():
            accuracy = get_accuracy(stats) * 100
            print(
                f"  {topic}: {accuracy:.1f}% correct ({stats['correct']}/{stats['attempted']})"
            )
    print("\nEnd of performance data.\n")
    input("Press Enter to return to main menu...")


# -------------------------------
# Main Program
# -------------------------------
def main_menu():
    performance = load_performance()

    while True:
        clear_screen()
        print("=== Adaptive Revision & Quiz System ===\n")
        print("Main Menu:")
        print("1. Start Quiz")
        print("2. View Performance")
        print("3. Exit")

        choice = input("\nEnter number: ").strip()
        if choice == "1":
            start_quiz(performance)
        elif choice == "2":
            view_performance(performance)
        elif choice == "3":
            print("Exiting program. Goodbye!")
            sys.exit()
        else:
            print("Invalid input. Please try again.\n")


def start_quiz(performance):
    clear_screen()
    # Level selection
    level = choose_option(LEVELS, "Choose qualification level:", allow_back=True)
    if level == "BACK":
        return

    clear_screen()
    # Subject selection
    subject = choose_option(SUBJECTS, "Choose subject:", allow_back=True)
    if subject == "BACK":
        return

    key = f"{level}_{subject}"
    if key not in performance:
        performance[key] = {}

    questions = load_questions(level, subject)
    if not questions:
        print("No questions found for this subject/level. Returning to main menu.\n")
        input("Press Enter to continue...")
        return

    print(f"\nStarting quiz: {level} {subject.replace('_', ' ')}\n")

    for question in questions:
        ask_question(question, performance, key)

    save_performance(performance)
    print("\n--- Session Summary ---")
    show_summary(performance[key])
    input("\nPress Enter to return to main menu...")


def show_summary(data):
    for topic, stats in data.items():
        accuracy = get_accuracy(stats) * 100
        print(
            f"{topic}: {accuracy:.1f}% correct ({stats['correct']}/{stats['attempted']})"
        )


# -------------------------------
# Run Program
# -------------------------------
if __name__ == "__main__":
    main_menu()
