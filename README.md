# Adaptive Revision & Quiz System - A-Level Computer Science Project (A* Version)

## Hello there! My name is Isaac Olukanni, I am an A-Level student at St. Cuthbert's Catholic High School's Sixth Form. This is my NEA Project built in Python.

This project is an advanced, adaptive educational tool designed for GCSE and A-Level students. It dynamically tracks student performance, utilizes complex algorithms for Spaced Repetition (SuperMemo-2), adjusts difficulty dynamically using an Elo Rating system, and features a modern Graphical User Interface (GUI).

---

## Key A* Features Implemented

1. **Modern Graphical User Interface (Event-Driven Programming)**
   - Built using `customtkinter` for a sleek, modern, dark-mode compatible UI.
   - Implements event-driven programming with dynamic frame switching (`LoginFrame`, `MainMenuFrame`, `QuizFrame`, `PerformanceFrame`).

2. **Relational Database Management System (RDBMS)**
   - Powered by a fully normalized **SQLite 3** database (`data/database.py`).
   - Adheres to **3rd Normal Form (3NF)** with tables for `Users`, `Subjects`, `Questions`, and `UserPerformance` linked via Foreign Keys.
   - Uses complex SQL queries (JOINs, aggregations) to handle data retrieval.

3. **Advanced Algorithmic Complexity (Spaced Repetition & Elo)**
   - **Spaced Repetition:** Calculates exponential backoff for review dates based on accuracy and past attempts (`models/adaptive.py`).
   - **Dynamic Difficulty Adjustment (Elo):** Users and questions both have "Elo ratings". Correctly answering hard questions significantly boosts a student's rating!

4. **Multi-User Authentication & Security**
   - Secure login and registration system.
   - Passwords are securely hashed using `hashlib` (SHA-256) preventing plain-text storage (a key cybersecurity requirement).

5. **Data Visualization**
   - Integrates **Matplotlib** directly into the CustomTkinter GUI.
   - Dynamically generates bar charts querying SQL data to show student accuracy percentages across different subjects and topics.

6. **Advanced String Processing & Fuzzy Matching**
   - A robust natural language processing engine (`models/evaluator.py`) evaluates free-text answers.
   - Includes Unicode NFKC normalization, numeric word parsing (e.g., converting "twenty one" to `21`), token extraction, and fuzzy matching (via `rapidfuzz` or `difflib` fallback) to forgive minor typos.

7. **Object-Oriented Programming (OOP) Architecture**
   - The entire codebase is strictly Object-Oriented, applying Encapsulation, Modularity, and Inheritance.

---

## Project Structure

- `main-revision_quiz/`
  - `main_gui.py` - **The primary entry point!** (CustomTkinter GUI application)
  - `main.py` - (The older CLI version of the app)
  - `data/`
    - `database.py` - SQLite schema and connection manager (CRUD ops)
    - `quiz_data.db` - The live 3NF database containing all questions and users
    - `migrate.py` - Script used to port the old JSON questions into SQLite
  - `models/`
    - `adaptive.py` - Spaced repetition & Elo calculation algorithms
    - `evaluator.py` - The NLP and fuzzy matching answer grading engine
- `README.md` - this file

---

## Dependencies & Installation

- Python 3.8+ recommended.
- Install the required libraries for the GUI, Graphing, and Fuzzy Matching:

```bash
pip install customtkinter matplotlib rapidfuzz
```
*(Note: If you are on a Mac and get an externally-managed-environment error, you can safely use the `--break-system-packages` flag for this project).*

---

## Running the Program

To launch the full graphical application, run:
```bash
python3 main-revision_quiz/main_gui.py
```

### How to use it:
1. **Register**: Create a new account on the login screen.
2. **Dashboard**: Navigate to the Main Menu.
3. **Take a Quiz**: Select a subject. Answer questions using the smart Answer Evaluator. Type `!exit` to quit a quiz early, or finish all 5 to see your summary.
4. **View Performance**: Go to the Performance Profile, select a subject you've taken a quiz in, and view your dynamically generated Matplotlib accuracy graph!

---

## Use of AI

This project made limited, explicit use of AI agents to format this README and provide questions for use in the program in the JSON format.
