import json
import os
import sys

import customtkinter as ctk

# Ensure imports work no matter where I run this script from
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database import DatabaseManager
from models.evaluator import AnswerEvaluator

# Try to import matplotlib. If it fails, we handle it gracefully!
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    MATPLOTLIB_INSTALLED = True
except ImportError:
    MATPLOTLIB_INSTALLED = False

# Set up the modern look. My teacher will love this!
ctk.set_appearance_mode("System")  # Follows the OS dark/light mode
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"


class QuizAppGUI(ctk.CTk):
    # This is the main window of the app. It inherits from CustomTkinter's CTk class.
    def __init__(self):
        super().__init__()

        self.title("Adaptive Revision Quiz - A* Project")
        self.geometry("800x600")
        self.minsize(600, 400)

        # Connect to the DB
        db_path = os.path.join(os.path.dirname(__file__), "data", "quiz_data.db")
        db_exists = os.path.exists(db_path)
        self.db = DatabaseManager(db_path)

        if not db_exists:
            print("=========================================================")
            print(" WARNING: quiz_data.db not found or is empty!")
            print(" Please run: python3 main-revision_quiz/data/migrate.py")
            print("=========================================================")

        # State variables
        self.current_user_id = None
        self.username = None

        # A dictionary to hold all my different screens (frames)
        self.frames = {}

        # Initialize the frames
        self.frames["Login"] = LoginFrame(self)
        self.frames["MainMenu"] = MainMenuFrame(self)
        self.frames["SubjectSelection"] = SubjectSelectionFrame(self)
        self.frames["Quiz"] = QuizFrame(self)
        self.frames["Summary"] = SummaryFrame(self)
        self.frames["Performance"] = PerformanceFrame(self)

        # Start by showing the login screen
        self.show_frame("Login")

    def show_frame(self, frame_name):
        # Hide all frames first
        for frame in self.frames.values():
            frame.pack_forget()

        # Then show the one I want
        frame_to_show = self.frames[frame_name]
        frame_to_show.pack(fill="both", expand=True)

        # Triggers for when specific frames load
        if frame_name == "MainMenu":
            frame_to_show.update_welcome_text()
        elif frame_name == "SubjectSelection":
            frame_to_show.load_subjects()
        elif frame_name == "Performance":
            frame_to_show.load_data()


class LoginFrame(ctk.CTkFrame):
    # This handles logging in and registering.
    def __init__(self, master):
        super().__init__(master)
        self.master = master  # Save a reference to the main window

        # UI Elements
        self.title_label = ctk.CTkLabel(
            self,
            text="Login to Revision System",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.pack(pady=(100, 20))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=250)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(
            self, placeholder_text="Password", show="*", width=250
        )
        self.password_entry.pack(pady=10)

        self.login_btn = ctk.CTkButton(
            self, text="Login", command=self.attempt_login, width=250
        )
        self.login_btn.pack(pady=10)

        self.register_btn = ctk.CTkButton(
            self,
            text="Register New User",
            command=self.attempt_register,
            width=250,
            fg_color="transparent",
            border_width=2,
        )
        self.register_btn.pack(pady=10)

        self.quit_btn = ctk.CTkButton(
            self,
            text="Quit App",
            command=self.master.destroy,
            width=250,
            fg_color="#8B0000",
            hover_color="#600000",
        )
        self.quit_btn.pack(pady=10)

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=10)

    def attempt_login(self):
        user = self.username_entry.get().strip()
        pw = self.password_entry.get().strip()

        uid = self.master.db.verify_user(user, pw)
        if uid:
            # Login success! Update state and swap screens.
            self.master.current_user_id = uid
            self.master.username = user
            self.error_label.configure(text="", text_color="green")
            self.username_entry.delete(0, "end")
            self.password_entry.delete(0, "end")
            self.master.show_frame("MainMenu")
        else:
            self.error_label.configure(
                text="Invalid credentials. Try again.", text_color="red"
            )

    def attempt_register(self):
        user = self.username_entry.get().strip()
        pw = self.password_entry.get().strip()

        if not user or not pw:
            self.error_label.configure(
                text="Username and password cannot be empty.", text_color="red"
            )
            return

        if self.master.db.create_user(user, pw):
            self.error_label.configure(
                text="Registration successful! You can now login.", text_color="green"
            )
        else:
            self.error_label.configure(
                text="Username already exists.", text_color="red"
            )


class MainMenuFrame(ctk.CTkFrame):
    # This is the hub menu shown after logging in.
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.welcome_label = ctk.CTkLabel(
            self, text="Welcome!", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.welcome_label.pack(pady=(80, 40))

        self.quiz_btn = ctk.CTkButton(
            self,
            text="Start Adaptive Quiz",
            font=ctk.CTkFont(size=16),
            height=50,
            width=300,
            command=self.start_quiz,
        )
        self.quiz_btn.pack(pady=10)

        self.perf_btn = ctk.CTkButton(
            self,
            text="View Performance Profile",
            font=ctk.CTkFont(size=16),
            height=50,
            width=300,
            command=self.view_performance,
        )
        self.perf_btn.pack(pady=10)

        self.logout_btn = ctk.CTkButton(
            self,
            text="Logout",
            fg_color="#b35b00",
            hover_color="#8c4700",
            font=ctk.CTkFont(size=16),
            height=50,
            width=300,
            command=self.logout,
        )
        self.logout_btn.pack(pady=10)

        self.quit_btn = ctk.CTkButton(
            self,
            text="Quit App",
            fg_color="#8B0000",
            hover_color="#600000",
            font=ctk.CTkFont(size=16),
            height=50,
            width=300,
            command=self.master.destroy,
        )
        self.quit_btn.pack(pady=10)

    def update_welcome_text(self):
        self.welcome_label.configure(
            text=f"Welcome to your dashboard, {self.master.username}!"
        )

    def logout(self):
        self.master.current_user_id = None
        self.master.username = None
        self.master.show_frame("Login")

    def start_quiz(self):
        self.master.show_frame("SubjectSelection")

    def view_performance(self):
        self.master.show_frame("Performance")


class PerformanceFrame(ctk.CTkFrame):
    # This renders the matplotlib graphs directly into CustomTkinter!
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title_label = ctk.CTkLabel(
            self, text="Performance Dashboard", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))

        # Controls container for the dropdown and back button
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(pady=5)

        self.subject_var = ctk.StringVar(value="Select Subject")
        self.subject_dropdown = ctk.CTkOptionMenu(
            self.controls_frame,
            variable=self.subject_var,
            command=self.on_subject_select,
            width=200,
        )
        self.subject_dropdown.pack(side="left", padx=10)

        self.back_btn = ctk.CTkButton(
            self.controls_frame,
            text="Go Back",
            fg_color="gray",
            command=lambda: self.master.show_frame("MainMenu"),
            width=100,
        )
        self.back_btn.pack(side="left", padx=10)

        # This frame will hold our matplotlib canvas
        self.graph_frame = ctk.CTkFrame(
            self, width=700, height=450, fg_color="transparent"
        )
        self.graph_frame.pack(pady=10, fill="both", expand=True)

        self.current_canvas = None
        self.subject_map = {}  # Maps dropdown string to subject_id

    def load_data(self):
        # Fetch only the subjects the user has actually attempted
        self.master.db.cursor.execute(
            """
            SELECT DISTINCT Subjects.id, Subjects.level, Subjects.name
            FROM Subjects
            JOIN Questions ON Subjects.id = Questions.subject_id
            JOIN UserPerformance ON Questions.id = UserPerformance.question_id
            WHERE UserPerformance.user_id = ?
            """,
            (self.master.current_user_id,),
        )
        subjects = self.master.db.cursor.fetchall()

        if not subjects:
            self.subject_dropdown.configure(values=["No Data Yet"], state="disabled")
            self.subject_var.set("No Data Yet")
            self.render_graph(None)
            return

        # Populate the dropdown options
        self.subject_map = {
            f"{level} - {name}": sub_id for sub_id, level, name in subjects
        }
        subject_names = list(self.subject_map.keys())

        self.subject_dropdown.configure(values=subject_names, state="normal")

        # Select the first subject by default and draw the graph
        first_subject = subject_names[0]
        self.subject_var.set(first_subject)
        self.render_graph(self.subject_map[first_subject])

    def on_subject_select(self, choice):
        if choice in self.subject_map:
            self.render_graph(self.subject_map[choice])

    def render_graph(self, subject_id):
        # Clear out the old graph if one exists
        if self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None

        if not MATPLOTLIB_INSTALLED:
            error_lbl = ctk.CTkLabel(
                self.graph_frame,
                text="Matplotlib is not installed!\nPlease run: pip install matplotlib",
                text_color="red",
            )
            error_lbl.pack(pady=100)
            return

        topics = []
        accuracies = []

        if subject_id is None:
            topics = ["No Data"]
            accuracies = [0]
        else:
            # Query accuracy just for this specific subject
            self.master.db.cursor.execute(
                """
                SELECT topic, SUM(attempts), SUM(correct)
                FROM Questions
                JOIN UserPerformance ON Questions.id = UserPerformance.question_id
                WHERE UserPerformance.user_id = ? AND Questions.subject_id = ?
                GROUP BY topic
            """,
                (self.master.current_user_id, subject_id),
            )

            results = self.master.db.cursor.fetchall()

            for row in results:
                topic = row[0]
                attempts = row[1]
                correct = row[2]
                acc = (correct / attempts) * 100 if attempts > 0 else 0
                topics.append(topic[:10] + "..")  # Shorten long topic names
                accuracies.append(acc)

        # --- Matplotlib Integration ---
        # Dark mode styling to match CustomTkinter
        plt.style.use("dark_background")

        fig, ax = plt.subplots(figsize=(7, 4), dpi=100)
        fig.patch.set_facecolor("#2b2b2b")  # Match CTk background
        ax.set_facecolor("#2b2b2b")

        # Create a bar chart
        bars = ax.bar(topics, accuracies, color="#1f6aa5")  # CustomTkinter blue

        ax.set_ylabel("Accuracy (%)", color="white")
        ax.set_title("Your Accuracy by Topic", color="white", pad=15)
        ax.set_ylim(0, 100)

        # Clean up the borders
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#555555")
        ax.spines["bottom"].set_color("#555555")

        # Add labels to the top of the bars
        ax.bar_label(bars, fmt="%.0f%%", padding=3, color="white")

        # Embed the Matplotlib figure into the Tkinter Frame
        self.current_canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        self.current_canvas.draw()

        widget = self.current_canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)


class SubjectSelectionFrame(ctk.CTkFrame):
    # This screen lets the user pick what they want to revise.
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title_label = ctk.CTkLabel(
            self, text="Select a Subject", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(40, 20))

        # I'm using a ScrollableFrame so if I add 50 subjects later, it won't break the UI!
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=400, height=350)
        self.scrollable_frame.pack(pady=10)

        self.back_btn = ctk.CTkButton(
            self,
            text="Go Back",
            fg_color="gray",
            command=lambda: self.master.show_frame("MainMenu"),
        )
        self.back_btn.pack(pady=20)

    def load_subjects(self):
        # Clear existing buttons first (in case they navigated back and forth)
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Fetch subjects from DB
        self.master.db.cursor.execute("SELECT id, level, name FROM Subjects")
        subjects = self.master.db.cursor.fetchall()

        if not subjects:
            no_sub_label = ctk.CTkLabel(
                self.scrollable_frame, text="No subjects found. Run migration script!"
            )
            no_sub_label.pack(pady=20)
            return

        for sub in subjects:
            sub_id, level, name = sub
            btn_text = f"{level} - {name}"
            # Need to capture the current sub_id in the lambda, so I use default arg i=sub_id
            btn = ctk.CTkButton(
                self.scrollable_frame,
                text=btn_text,
                font=ctk.CTkFont(size=14),
                height=40,
                command=lambda i=sub_id: self.select_subject(i),
            )
            btn.pack(pady=5, fill="x", padx=20)

    def select_subject(self, subject_id):
        # Pull 5 random questions
        self.master.db.cursor.execute(
            "SELECT id, topic, question_text, answer_text, difficulty FROM Questions WHERE subject_id = ? ORDER BY RANDOM() LIMIT 5",
            (subject_id,),
        )
        questions = self.master.db.cursor.fetchall()

        if not questions:
            # If a subject has no questions somehow
            return

        # Pass questions to the quiz frame and start!
        self.master.frames["Quiz"].start_new_quiz(questions)
        self.master.show_frame("Quiz")


class QuizFrame(ctk.CTkFrame):
    # This is the actual quiz interface!
    # Event-driven programming makes this much cooler than the CLI.
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.questions = []
        self.current_q_index = 0
        self.score = 0
        self.current_answers = []

        # UI Elements
        self.header_label = ctk.CTkLabel(
            self,
            text="Topic: ... | Difficulty: ...",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        self.header_label.pack(pady=(40, 10))

        # Using textbox for question so it wraps text automatically if it's long
        self.question_text = ctk.CTkTextbox(
            self, width=600, height=100, font=ctk.CTkFont(size=18), wrap="word"
        )
        self.question_text.pack(pady=10)
        self.question_text.configure(state="disabled")  # Make it read-only

        self.answer_entry = ctk.CTkEntry(
            self,
            placeholder_text="Type your answer here...",
            width=400,
            height=40,
            font=ctk.CTkFont(size=16),
        )
        self.answer_entry.pack(pady=20)

        # Bind the Enter key to the submit button
        self.answer_entry.bind("<Return>", lambda event: self.submit_answer())

        self.submit_btn = ctk.CTkButton(
            self, text="Submit Answer", width=200, height=40, command=self.submit_answer
        )
        self.submit_btn.pack(pady=10)

        # --- Flashcard UI Elements (Hidden by default) ---
        self.reveal_btn = ctk.CTkButton(
            self,
            text="Reveal Answer",
            width=200,
            height=40,
            fg_color="#b35b00",
            hover_color="#8c4700",
            command=self.reveal_answer,
        )

        self.self_grade_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.correct_btn = ctk.CTkButton(
            self.self_grade_frame,
            text="✅ I knew it",
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: self.submit_self_grade(True),
            width=140,
        )
        self.correct_btn.pack(side="left", padx=10)
        self.wrong_btn = ctk.CTkButton(
            self.self_grade_frame,
            text="❌ I didn't know it",
            fg_color="red",
            hover_color="darkred",
            command=lambda: self.submit_self_grade(False),
            width=140,
        )
        self.wrong_btn.pack(side="left", padx=10)
        # -------------------------------------------------

        self.feedback_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.feedback_label.pack(pady=10)

        self.elo_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12, slant="italic")
        )
        self.elo_label.pack(pady=5)

        self.next_btn = ctk.CTkButton(
            self,
            text="Next Question",
            width=200,
            height=40,
            fg_color="green",
            hover_color="darkgreen",
            command=self.next_question,
        )
        self.next_btn.pack(pady=10)
        self.next_btn.pack_forget()  # Hide it until they submit an answer

        self.exit_btn = ctk.CTkButton(
            self,
            text="Exit Quiz Early",
            fg_color="red",
            hover_color="darkred",
            command=lambda: self.master.show_frame("MainMenu"),
        )
        self.exit_btn.pack(pady=(30, 0))

    def start_new_quiz(self, questions):
        self.questions = questions
        self.current_q_index = 0
        self.score = 0
        self.load_question()

    def load_question(self):
        # Reset UI for the new question
        self.feedback_label.configure(text="")
        self.elo_label.configure(text="")

        self.answer_entry.pack_forget()
        self.submit_btn.pack_forget()
        self.reveal_btn.pack_forget()
        self.self_grade_frame.pack_forget()
        self.next_btn.pack_forget()

        q_id, topic, text, ans_text, diff = self.questions[self.current_q_index]
        self.current_q_id = q_id
        self.current_diff = diff

        self.header_label.configure(
            text=f"Question {self.current_q_index + 1} of {len(self.questions)} | Topic: {topic} | Difficulty: {diff}"
        )

        self.question_text.configure(state="normal")
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", text)
        self.question_text.configure(state="disabled")

        # Parse answers safely
        try:
            self.current_answers = json.loads(ans_text)
            if not isinstance(self.current_answers, list):
                self.current_answers = [str(self.current_answers)]
        except (json.JSONDecodeError, TypeError):
            self.current_answers = [ans_text]

        # Determine if this is a "Long Answer" (e.g., > 30 characters)
        # If it's a long answer, we use Flashcard Mode instead of typing.
        self.is_long_answer = len(str(self.current_answers[0])) > 30

        if self.is_long_answer:
            self.reveal_btn.pack(pady=10, before=self.feedback_label)
            self.feedback_label.configure(
                text="Flashcard Mode: Think of the answer in your head, then reveal it.",
                text_color="orange",
            )
        else:
            self.submit_btn.pack(pady=10, before=self.feedback_label)
            self.answer_entry.pack(pady=20, before=self.submit_btn)
            self.answer_entry.configure(state="normal")
            self.answer_entry.delete(0, "end")

    def submit_answer(self):
        # Prevent multiple submits
        if self.answer_entry.cget("state") == "disabled":
            return

        user_ans = self.answer_entry.get().strip()
        if not user_ans:
            return  # Ignore empty submits

        # Grade it!
        is_correct, matched_ans = AnswerEvaluator.evaluate(
            user_ans, self.current_answers
        )

        if is_correct:
            self.score += 1
            if matched_ans and matched_ans != user_ans:
                self.feedback_label.configure(
                    text=f"✅ Correct! (I accepted: {matched_ans})", text_color="green"
                )
            else:
                self.feedback_label.configure(text="✅ Correct!", text_color="green")
        else:
            display_correct = ", ".join(str(a) for a in self.current_answers)
            self.feedback_label.configure(
                text=f"❌ Incorrect. The right answer was:\n{display_correct}",
                text_color="red",
            )

        self._save_performance(is_correct)

        # Lock the entry box and show the next button
        self.answer_entry.configure(state="disabled")
        self.submit_btn.pack_forget()
        self.next_btn.pack(pady=10, before=self.exit_btn)

    def reveal_answer(self):
        # Called in Flashcard Mode when they click "Reveal"
        self.reveal_btn.pack_forget()
        display_correct = ", ".join(str(a) for a in self.current_answers)
        self.feedback_label.configure(
            text=f"Correct Answer:\n{display_correct}", text_color="white"
        )
        self.self_grade_frame.pack(pady=10, before=self.elo_label)

    def submit_self_grade(self, is_correct):
        # Called when they click Yes/No in Flashcard mode
        self.self_grade_frame.pack_forget()

        if is_correct:
            self.score += 1
            self.feedback_label.configure(
                text="✅ Marked as Correct!", text_color="green"
            )
        else:
            self.feedback_label.configure(
                text="❌ Marked as Incorrect.", text_color="red"
            )

        self._save_performance(is_correct)
        self.next_btn.pack(pady=10, before=self.exit_btn)

    def _save_performance(self, is_correct):
        # --- SAVE TO DATABASE ---
        user_id = self.master.current_user_id
        q_id = self.current_q_id

        # Check if they have answered this question before
        self.master.db.cursor.execute(
            "SELECT attempts, correct FROM UserPerformance WHERE user_id=? AND question_id=?",
            (user_id, q_id),
        )
        row = self.master.db.cursor.fetchone()

        if row:
            attempts, correct = row
            attempts += 1
            if is_correct:
                correct += 1
            self.master.db.cursor.execute(
                "UPDATE UserPerformance SET attempts=?, correct=? WHERE user_id=? AND question_id=?",
                (attempts, correct, user_id, q_id),
            )
        else:
            attempts = 1
            correct = 1 if is_correct else 0
            self.master.db.cursor.execute(
                "INSERT INTO UserPerformance (user_id, question_id, attempts, correct) VALUES (?, ?, ?, ?)",
                (user_id, q_id, attempts, correct),
            )
        self.master.db.conn.commit()
        # ------------------------

        self.elo_label.configure(
            text="-> Adaptive Engine: Database updated with your results.",
            text_color="gray",
        )

    def next_question(self):
        self.current_q_index += 1
        if self.current_q_index < len(self.questions):
            self.load_question()
        else:
            # End of quiz! Transition to summary.
            self.master.frames["Summary"].show_summary(self.score, len(self.questions))
            self.master.show_frame("Summary")


class SummaryFrame(ctk.CTkFrame):
    # Shown when a quiz finishes so they can see their score.
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title_label = ctk.CTkLabel(
            self, text="Quiz Complete!", font=ctk.CTkFont(size=32, weight="bold")
        )
        self.title_label.pack(pady=(100, 20))

        self.score_label = ctk.CTkLabel(
            self, text="Score: 0 / 0", font=ctk.CTkFont(size=24)
        )
        self.score_label.pack(pady=20)

        self.message_label = ctk.CTkLabel(
            self,
            text="Your performance has been recorded by the Adaptive Engine.",
            font=ctk.CTkFont(size=16),
            text_color="gray",
        )
        self.message_label.pack(pady=10)

        self.menu_btn = ctk.CTkButton(
            self,
            text="Return to Main Menu",
            width=250,
            height=50,
            font=ctk.CTkFont(size=16),
            command=lambda: self.master.show_frame("MainMenu"),
        )
        self.menu_btn.pack(pady=40)

    def show_summary(self, score, total):
        self.score_label.configure(text=f"Score: {score} / {total}")

        # Add a little encouraging message
        if score == total:
            self.message_label.configure(
                text="Perfect score! Your Elo rating is going to skyrocket! 🚀"
            )
        elif score >= total / 2:
            self.message_label.configure(
                text="Good job! Keep reviewing to improve your Elo rating."
            )
        else:
            self.message_label.configure(
                text="Tough questions! The Spaced Repetition engine will show these to you again soon."
            )


if __name__ == "__main__":
    # Event-driven programming start point
    app = QuizAppGUI()
    app.mainloop()
