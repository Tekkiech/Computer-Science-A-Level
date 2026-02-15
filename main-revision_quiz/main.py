import difflib
import json
import os
import re
import sys
import unicodedata
from typing import Optional

# Try to use rapidfuzz for fuzzy matching if available; fallback to difflib
try:
    # rapidfuzz is optional; if present we use its token-based ratio for better results
    from rapidfuzz import fuzz  # type: ignore

    _HAS_RAPIDFUZZ = True
except Exception:
    # Ensure `fuzz` exists even if rapidfuzz is missing so runtime checks won't fail
    fuzz = None
    _HAS_RAPIDFUZZ = False

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
    """
    Ask a question and perform robust answer matching:
    - normalization (case, punctuation, whitespace)
    - option-letter normalization (A, a., a) -> 'a')
    - numeric matching (words -> numbers and numeric parsing)
    - substring matching on normalized text
    - fuzzy matching with a conservative threshold
    """

    # --- Helper functions (kept local to avoid polluting global namespace) ---
    def normalize_text(s: str) -> str:
        if s is None:
            return ""
        s = str(s)
        s = unicodedata.normalize("NFKC", s)
        s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        s = s.strip().lower()
        # keep only ascii alphanumerics and spaces
        s = re.sub(r"[^0-9a-z\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def normalize_option(s: str) -> str:
        s = normalize_text(s)
        if not s:
            return ""
        parts = s.split()
        first = parts[0]
        m = re.match(r"^([a-zA-Z0-9])[\.\)]?$", first)
        if m:
            return m.group(1)
        return s

    _WORD_NUMS = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }

    def word_number_to_int(s: str) -> Optional[int]:
        s = normalize_text(s)
        if not s:
            return None
        parts = s.split()
        total = 0
        i = 0
        while i < len(parts):
            w = parts[i]
            if w in _WORD_NUMS:
                val = _WORD_NUMS[w]
                # handle "twenty one"
                if (
                    val >= 20
                    and i + 1 < len(parts)
                    and parts[i + 1] in _WORD_NUMS
                    and _WORD_NUMS[parts[i + 1]] < 10
                ):
                    total += val + _WORD_NUMS[parts[i + 1]]
                    i += 2
                    continue
                total += val
                i += 1
            else:
                return None
        return total

    def is_numeric(s: str) -> Optional[float]:
        s_norm = normalize_text(s)
        if not s_norm:
            return None
        try:
            return float(s_norm)
        except ValueError:
            pass
        wn = word_number_to_int(s_norm)
        if wn is not None:
            return float(wn)
        return None

    def _fuzzy_ratio(a: str, b: str) -> float:
        # Return similarity ratio in range 0..100.
        # Use rapidfuzz.token_sort_ratio when available and functioning,
        # otherwise fall back to difflib scaled to 0..100.
        try:
            if (
                _HAS_RAPIDFUZZ
                and fuzz is not None
                and hasattr(fuzz, "token_sort_ratio")
            ):
                # rapidfuzz's token_sort_ratio typically returns 0..100
                score = fuzz.token_sort_ratio(a, b)
                return float(score)
        except Exception:
            # If rapidfuzz exists but calling it fails, fall back to difflib
            pass
        # difflib returns 0..1, scale to 0..100
        return difflib.SequenceMatcher(None, a, b).ratio() * 100.0

    # --- End helpers ---

    topic = question["topic"]
    correct_answer = question["answer"]

    # Keep original forms for display, but accept lists or single answers
    if isinstance(correct_answer, list):
        correct_answers_raw = correct_answer
    else:
        correct_answers_raw = [correct_answer]

    user_answer_raw = input("\n" + question["question"] + " ")
    user_norm = normalize_text(user_answer_raw)
    user_option = normalize_option(user_answer_raw)

    if topic not in performance[key]:
        performance[key][topic] = {"attempted": 0, "correct": 0}

    performance[key][topic]["attempted"] += 1

    accepted = False
    matched = None
    fuzzy_threshold = 88.0  # tune this (higher -> stricter)

    for ca_raw in correct_answers_raw:
        ca_norm = normalize_text(ca_raw)
        ca_option = normalize_option(ca_raw)

        # 1) exact normalized match
        if user_norm and ca_norm and user_norm == ca_norm:
            accepted = True
            matched = ca_raw
            break

        # 2) option-letter/number equivalence (A vs "a.", "a)")
        if user_option and ca_option and user_option == ca_option:
            accepted = True
            matched = ca_raw
            break

        # 3) numeric matching (numbers spelled out or digits)
        ua_num = is_numeric(user_answer_raw)
        ca_num = is_numeric(ca_raw)
        if ua_num is not None and ca_num is not None:
            # exact numeric equality (could be relaxed with tolerance if desired)
            if abs(ua_num - ca_num) < 1e-9:
                accepted = True
                matched = ca_raw
                break

        # 4) containment of normalized correct answer inside user response (helps short answers)
        if ca_norm and ca_norm in user_norm:
            accepted = True
            matched = ca_raw
            break

        # 5) fuzzy match on normalized text (conservative threshold)
        if ca_norm and user_norm:
            score = _fuzzy_ratio(user_norm, ca_norm)
            if score >= fuzzy_threshold:
                accepted = True
                matched = ca_raw
                break

    if accepted:
        # Use the matched correct answer in the success message when available
        if matched:
            print(f"✅ Correct! (accepted: {matched})\n")
        else:
            print("✅ Correct!\n")
        performance[key][topic]["correct"] += 1
    else:
        # Show the original correct answers (unmodified) to the user
        display_correct = ", ".join(str(a) for a in correct_answers_raw)
        print(f"❌ Incorrect. Correct answer: {display_correct}\n")


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
