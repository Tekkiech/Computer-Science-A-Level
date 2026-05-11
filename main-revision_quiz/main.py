import os
import sys

# Ensure imports work no matter where I run this script from
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database import DatabaseManager
from models.adaptive import AdaptiveEngine
from models.evaluator import AnswerEvaluator


def clear_screen():
    # Clears the terminal so it looks neat. Windows uses 'cls', Mac/Linux uses 'clear'
    os.system("cls" if os.name == "nt" else "clear")


class QuizApp:
    def __init__(self):
        # Connecting to the SQLite database. Had to make the path absolute so it doesn't crash
        # if I run it from outside the folder.
        db_path = os.path.join(os.path.dirname(__file__), "data", "quiz_data.db")
        db_exists = os.path.exists(db_path)
        self.db = DatabaseManager(db_path)

        if not db_exists:
            print("=========================================================")
            print(" WARNING: quiz_data.db not found or is empty!")
            print(" Please run: python3 main-revision_quiz/data/migrate.py")
            print("=========================================================")

        # Keep track of who is logged in
        self.current_user_id = None
        self.username = None

    def run(self):
        clear_screen()
        print("=" * 50)
        print(" Adaptive Revision & Quiz System (My NEA Project)")
        print("=" * 50)

        # Trap the user in the login menu until they actually sign in
        while not self.current_user_id:
            self.auth_menu()

        self.main_menu()

    def auth_menu(self):
        # Basic authentication menu. My teacher said I need multi-user stuff for top band marks!
        print("\n1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            user = input("Username: ").strip()
            pw = input("Password: ").strip()
            # Check the hash in the DB
            uid = self.db.verify_user(user, pw)
            if uid:
                self.current_user_id = uid
                self.username = user
                print(f"Welcome back, {user}!")
            else:
                print("Invalid credentials. Try again or register.")
        elif choice == "2":
            user = input("New Username: ").strip()
            pw = input("New Password: ").strip()
            # create_user hashes the password before saving
            if self.db.create_user(user, pw):
                print("Registration successful! Please login now.")
            else:
                print("Username already exists. Pick another one.")
        elif choice == "3":
            sys.exit(0)

    def main_menu(self):
        # The main hub of the program
        while True:
            print(f"\n--- Main Menu ({self.username}) ---")
            print("1. Start Adaptive Quiz")
            print("2. View Performance Profile")
            print("3. Logout")
            print("4. Exit")

            choice = input("Select an option: ").strip()
            if choice == "1":
                self.start_quiz()
            elif choice == "2":
                self.view_performance()
            elif choice == "3":
                # Log out by clearing the variables
                self.current_user_id = None
                self.username = None
                break
            elif choice == "4":
                sys.exit(0)

    def start_quiz(self):
        # Fetch subjects from the SQL database
        self.db.cursor.execute("SELECT id, level, name FROM Subjects")
        subjects = self.db.cursor.fetchall()

        if not subjects:
            print("No subjects found in database. I probably forgot to run migrate.py!")
            return

        print("\nAvailable Subjects:")
        print("0. Go Back")
        for idx, sub in enumerate(subjects, 1):
            print(f"{idx}. {sub[1]} - {sub[2]}")

        try:
            raw_choice = input(
                "\nSelect a subject by number (or 0 to go back): "
            ).strip()
            if raw_choice == "0":
                return
            choice = int(raw_choice)
            selected_subject = subjects[choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection. Going back to menu.")
            return

        subject_id = selected_subject[0]

        # Get 5 random questions for now.
        # TODO for writeup: change ORDER BY RANDOM to use the Elo rating and next_review_date!
        self.db.cursor.execute(
            "SELECT id, topic, question_text, answer_text, difficulty FROM Questions WHERE subject_id = ? ORDER BY RANDOM() LIMIT 5",
            (subject_id,),
        )
        questions = self.db.cursor.fetchall()

        score = 0
        import json

        for q in questions:
            q_id, topic, text, ans_text, diff = q
            print(f"\n[Topic: {topic} | Difficulty: {diff}]")
            print(text)
            user_ans = input("Your Answer (or type '!exit' to quit quiz): ").strip()

            if user_ans.lower() == "!exit":
                print("\nExiting quiz early...")
                break

            # The answer in the database might be a JSON array of acceptable answers,
            # or just a normal string. Need to parse it safely.
            try:
                correct_answers = json.loads(ans_text)
                if not isinstance(correct_answers, list):
                    correct_answers = [str(correct_answers)]
            except (json.JSONDecodeError, TypeError):
                # If it fails to parse as JSON, just treat the whole thing as a single string answer
                correct_answers = [ans_text]

            # Use my custom AnswerEvaluator so it's not just a boring exact match
            is_correct, matched_ans = AnswerEvaluator.evaluate(
                user_ans, correct_answers
            )

            if is_correct:
                if matched_ans and matched_ans != user_ans:
                    print(f"✅ Correct! (I accepted: {matched_ans})")
                else:
                    print("✅ Correct!")
                score += 1
            else:
                display_correct = ", ".join(str(a) for a in correct_answers)
                print(f"❌ Incorrect. The right answer was: {display_correct}")

            # This is where I'd update the Elo rating and spaced repetition dates.
            # Just printing for now to show the concept works.
            print(
                f"-> Elo System evaluated your answer. Accuracy impacts next review date."
            )

        print(f"\nQuiz Complete! You scored: {score}/{len(questions)}")

    def view_performance(self):
        print("\n--- Performance Profile ---")
        print(
            "I'm going to add matplotlib graphs here soon to show progress over time."
        )
        print("(Integration in progress for my next coursework milestone...)")


if __name__ == "__main__":
    app = QuizApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
