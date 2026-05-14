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

4. **Semantic AI Grading (Generative SLM)**
   - Automatically grades free-text and long-answer questions using a local Small Language Model (SLM) via `llama-cpp-python` and GGUF quantization.
   - Non-blocking evaluation: Asynchronously infers the correctness of a user's answer, displaying a "Checking..." indicator before providing structured "CORRECT" or "WRONG" explanations.
   - Automatically downloads the quantized AI models from Hugging Face hub locally on the first run.

5. **Multi-User Authentication & Security**
   - Secure login and registration system.
   - Passwords are securely hashed using `hashlib` (SHA-256) preventing plain-text storage (a key cybersecurity requirement).

6. **Data Visualization**
   - Integrates **Matplotlib** directly into the CustomTkinter GUI.
   - Dynamically generates bar charts querying SQL data to show student accuracy percentages across different subjects and topics.

7. **Advanced String Processing & Fuzzy Matching**
   - A robust natural language processing engine (`models/evaluator.py`) evaluates free-text answers.
   - Includes Unicode NFKC normalization, numeric word parsing (e.g., converting "twenty one" to `21`), token extraction, and fuzzy matching (via `rapidfuzz` or `difflib` fallback) to forgive minor typos.

8. **Object-Oriented Programming (OOP) Architecture**
   - The entire codebase is strictly Object-Oriented, applying Encapsulation, Modularity, and Inheritance.

---

## Project Structure

- `main-revision_quiz/`
  - `main_gui.py` - **The primary entry point!** (CustomTkinter GUI application)
  - `data/`
    - `database.py` - SQLite schema and connection manager (CRUD ops)
    - `migrate.py` - Script used to port the JSON questions into the SQLite database. Run this first!
  - `models/`
    - `adaptive.py` - Spaced repetition & Elo calculation algorithms
    - `evaluator.py` - The NLP, fuzzy matching, and Semantic AI grading engine
  - `questions/` - JSON files storing all questions for A-Level and GCSE subjects
- `requirements.txt` - Project dependencies
- `README.md` - this file

---

## Dependencies & Installation

- Python 3.8+ recommended.

It is highly recommended to set up a virtual environment for a clean fresh-start:

```bash
# 1. Create a virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 3. Install the required dependencies
pip install -r requirements.txt
```

*(Note: The first time you encounter a long-answer question in the quiz, the app will automatically download a quantized GGUF model into `main-revision_quiz/models/`. This requires an internet connection and will download roughly 1.6GB of data.)*

---

## Initializing the Database

Before launching the application for the first time, you must run the migration script to populate the SQLite database with the JSON questions.

```bash
python3 main-revision_quiz/data/migrate.py
```
This will create a `quiz_data.db` file in the `data/` folder.

---

## Running the Program

To launch the full graphical application, run:
```bash
python3 main-revision_quiz/main_gui.py
```

### How to use it:
1. **Register**: Create a new account on the login screen.
2. **Dashboard**: Navigate to the Main Menu.
3. **Take a Quiz**: Select a subject. You can configure the long-answer threshold via the slider. Answer questions using the smart Answer Evaluator, which will trigger the AI semantics checker for complex answers.
4. **View Performance**: Go to the Performance Profile, select a subject you've taken a quiz in, and view your dynamically generated Matplotlib accuracy graph!

---

## Use of AI

This project made limited, explicit use of AI agents to format this README and to generate questions for use in the program in the JSON format. AI models (Qwen) were additionally integrated strictly locally (no remote API calls) specifically to enhance the educational evaluation engine, operating within typical user hardware limits.
