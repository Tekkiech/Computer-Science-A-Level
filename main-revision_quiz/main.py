import difflib
import json
import os
import random
import re
import sys
import unicodedata
from typing import Optional

# rapidfuzz is optional. If missing we use difflib.
try:
    from rapidfuzz import fuzz 

    _HAS_RAPIDFUZZ = True
except Exception:
    fuzz = None
    _HAS_RAPIDFUZZ = False

# Config
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


def clear_screen():
    """Clear the terminal for a tidy UI."""
    os.system("cls" if os.name == "nt" else "clear")


def load_questions(level, subject):
    """load questions JSON for the given level and subject.
    Return [] if file not found."""
    filename = f"{level}_{subject}.json"
    path = os.path.join(QUESTIONS_DIR, filename)
    if not os.path.exists(path):
        print(f"Error: {filename} not found in {QUESTIONS_DIR}")
        return []
    with open(path, "r") as file:
        return json.load(file)


def load_performance():
    """read performance.json. Return {} if missing or empty.
    If corrupted, warn and start fresh."""
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
    """save performance to disk as pretty JSON."""
    with open(PERFORMANCE_FILE, "w") as file:
        json.dump(performance, file, indent=4)


def choose_option(options, prompt, allow_back=False):
    """show a simple numbered menu and return the chosen option."""
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
    """Return accuracy as 0..1."""
    if data["attempted"] == 0:
        return 0
    return data["correct"] / data["attempted"]


def ask_question(question, performance, key):
    """ask a question, accept flexible answers, and update performance.

    Matching is forgiving to help revision:
    - normalize text
    - accept option tokens like 'a)' or '1.'
    - accept small numeric variants like 'three' vs '3'
    - allow short token containment
    - use conservative fuzzy match for minor typos
    """

    def normalize_text(s: str) -> str:
        """Lowercase, NFKC, remove weird punctuation, keep alphanum and spaces."""
        if s is None:
            return ""
        s = str(s)
        s = unicodedata.normalize("NFKC", s)
        # replace some smart quotes with plain ones
        s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        s = s.strip().lower()
        s = re.sub(r"[^0-9a-z\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def normalize_option(s: str) -> str:
        """Get a single option token like 'a' or '1' if present."""
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
        """Convert simple word numbers like 'twenty one' to int, or None."""
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
        """Try float conversion or small word number conversion."""
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
        """Return similarity 0..100. Prefer rapidfuzz if available."""
        try:
            if (
                _HAS_RAPIDFUZZ
                and fuzz is not None
                and hasattr(fuzz, "token_sort_ratio")
            ):
                score = fuzz.token_sort_ratio(a, b)
                return float(score)
        except Exception:
            pass
        return difflib.SequenceMatcher(None, a, b).ratio() * 100.0

    topic = question["topic"]
    correct_answer = question["answer"]

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
    fuzzy_threshold = 88.0

    for ca_raw in correct_answers_raw:
        ca_norm = normalize_text(ca_raw)
        ca_option = normalize_option(ca_raw)

        # 1) exact normalized match
        if user_norm and ca_norm and user_norm == ca_norm:
            accepted = True
            matched = ca_raw
            break

        # 2) option token match
        if user_option and ca_option and user_option == ca_option:
            accepted = True
            matched = ca_raw
            break

        # 3) numeric match
        ua_num = is_numeric(user_answer_raw)
        ca_num = is_numeric(ca_raw)
        if ua_num is not None and ca_num is not None:
            if abs(ua_num - ca_num) < 1e-9:
                accepted = True
                matched = ca_raw
                break

        # 4) containment: short token inside longer reply
        if ca_norm and ca_norm in user_norm:
            accepted = True
            matched = ca_raw
            break

        # 5) fuzzy match for small typos
        if ca_norm and user_norm:
            score = _fuzzy_ratio(user_norm, ca_norm)
            if score >= fuzzy_threshold:
                accepted = True
                matched = ca_raw
                break

    if accepted:
        if matched:
            print(f"✅ Correct! (accepted: {matched})\n")
        else:
            print("✅ Correct!\n")
        performance[key][topic]["correct"] += 1
    else:
        display_correct = ", ".join(str(a) for a in correct_answers_raw)
        print(f"❌ Incorrect. Correct answer: {display_correct}\n")


def view_performance(performance):
    """Show a compact report of recorded performance."""
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


def clear_performance(performance):
    """Clear the performance data file and in-memory performance after confirmation."""
    clear_screen()
    print("WARNING: This will permanently delete all recorded performance data.\n")
    print(
        "If you want to proceed, type 'YES' (uppercase). To cancel, press Enter or type anything else."
    )
    confirm = input("Confirm clear performance: ").strip()
    if confirm == "YES":
        # Try removing the file if it exists, then reset in-memory data and save an empty file.
        try:
            if os.path.exists(PERFORMANCE_FILE):
                os.remove(PERFORMANCE_FILE)
        except Exception as e:
            print(f"Could not remove performance file: {e}")
            input("\nPress Enter to return to main menu...")
            return
        performance.clear()
        # Ensure an empty JSON object is written so the application has a valid file next run.
        save_performance(performance)
        print("\nAll performance data has been cleared.\n")
    else:
        print("\nClear operation cancelled. No changes made.\n")
    input("Press Enter to return to main menu...")


def main_menu():
    """Top level menu to start quizzes or view performance."""
    performance = load_performance()

    while True:
        clear_screen()
        print("=== Adaptive Revision & Quiz System ===\n")
        print("Main Menu:")
        print("1. Start Quiz")
        print("2. View Performance")
        print("3. Clear Performance")
        print("4. Exit")

        choice = input("\nEnter number: ").strip()
        if choice == "1":
            start_quiz(performance)
        elif choice == "2":
            view_performance(performance)
        elif choice == "3":
            clear_performance(performance)
        elif choice == "4":
            print("Exiting program. Goodbye!")
            sys.exit()
        else:
            print("Invalid input. Please try again.\n")


def _get_available_difficulties(questions):
    """Return a sorted list of difficulties present in questions, prefixed by 'Any'."""
    diffs = set()
    for q in questions:
        d = q.get("difficulty")
        if d is None:
            continue
        diffs.add(str(d))
    # define a preferred ordering if common levels found
    order = ["Easy", "Medium", "Hard"]
    present_ordered = [d for d in order if d in diffs]
    # add any remaining difficulties sorted alphabetically
    remaining = sorted([d for d in diffs if d not in present_ordered])
    options = ["Any"] + present_ordered + remaining
    return options


def _choose_question_count(max_count):
    """Prompt user for number of questions to use. Accepts a number or 'all'."""
    while True:
        resp = (
            input(
                f"Enter number of questions to attempt (1-{max_count}) or 'all' to use all: "
            )
            .strip()
            .lower()
        )
        if resp in ("all", ""):
            return max_count
        if resp.isdigit():
            n = int(resp)
            if 1 <= n <= max_count:
                return n
        print("Invalid input. Please enter a valid number or 'all'.")


def start_quiz(performance):
    """Run a quiz session for a chosen level and subject, with difficulty and count selection."""
    clear_screen()
    level = choose_option(LEVELS, "Choose qualification level:", allow_back=True)
    if level == "BACK":
        return

    clear_screen()
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

    # Filter selection menu: None / Difficulty / Marks
    filters = ["None", "Difficulty", "Marks"]
    clear_screen()
    filter_choice = choose_option(filters, "Filter questions by:", allow_back=True)
    if filter_choice == "BACK":
        return

    filtered = list(questions)
    filter_info = "None"

    if filter_choice == "Difficulty":
        # Difficulty sub-selection (re-uses helper)
        difficulties = _get_available_difficulties(questions)
        clear_screen()
        difficulty_choice = choose_option(
            difficulties, "choose difficulty (Any = all difficulties):", allow_back=True
        )
        if difficulty_choice == "BACK":
            return

        filter_info = f"difficulty: {difficulty_choice}"
        if difficulty_choice == "Any":
            filtered = list(questions)
        else:
            filtered = [
                q for q in questions if str(q.get("difficulty")) == difficulty_choice
            ]

        if not filtered:
            print(
                f"no questions found for difficulty '{difficulty_choice}'. returning to main menu.\n"
            )
            input("press enter to continue...")
            return

    elif filter_choice == "Marks":
        # Ask user for a marks filter: exact value, range like '1-2', or 'all' to cancel
        clear_screen()
        while True:
            resp = (
                input(
                    "enter marks to filter (e.g. '1'), a range '1-2', or 'all' to include all marks: "
                )
                .strip()
                .lower()
            )
            if resp == "all" or resp == "":
                filtered = list(questions)
                filter_info = "marks: all"
                break
            # range form
            if "-" in resp:
                parts = resp.split("-", 1)
                if parts[0].isdigit() and parts[1].isdigit():
                    lo = int(parts[0])
                    hi = int(parts[1])
                    if lo > hi:
                        lo, hi = hi, lo
                    filtered = [
                        q
                        for q in questions
                        if isinstance(q.get("marks"), int)
                        and lo <= q.get("marks") <= hi
                    ]
                    filter_info = f"Marks: {lo}-{hi}"
                    break
            # single integer
            if resp.isdigit():
                m = int(resp)
                filtered = [q for q in questions if q.get("marks") == m]
                filter_info = f"Marks: {m}"
                break

            print("invalid input. enter a number, range like '1-2', or 'all'.")

        if not filtered:
            print(
                "no questions found for the selected marks. returning to main menu.\n"
            )
            input("Press Enter to continue...")
            return

    # Choose number of questions
    clear_screen()
    total_available = len(filtered)
    print(f"\n{total_available} questions available ({filter_info})\n")
    count = _choose_question_count(total_available)

    # Randomly select requested number of questions
    if count >= total_available:
        random.shuffle(filtered)
        selected_questions = filtered
    else:
        selected_questions = random.sample(filtered, count)

    print(
        f"\nstarting quiz: {level} {subject.replace('_', ' ')} — {filter_info} — Questions: {len(selected_questions)}\n"
    )

    for question in selected_questions:
        ask_question(question, performance, key)

    save_performance(performance)
    print("\nSession Summary")
    show_summary(performance[key])
    input("\nPress Enter to return to main menu...")


def show_summary(data):
    """print topic by topic accuracy for the session."""
    for topic, stats in data.items():
        accuracy = get_accuracy(stats) * 100
        print(
            f"{topic}: {accuracy:.1f}% correct ({stats['correct']}/{stats['attempted']})"
        )


if __name__ == "__main__":
    main_menu()
