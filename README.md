# Adaptive Revision & Quiz System - A-Level Computer Science Project

Simple CLI quiz tool in Python. Use it to practice GCSE and A-Level topics.
The app is intentionally small and self-contained so it's easy to read, run and
explain in a coursework viva.

This README describes the current features (filters, question count, clear
performance), data format, and how to run the program.

---

## Quick overview of features

- Choose qualification level (GCSE, ALevel) and subject.
- Filter questions by:
  - Difficulty (`Easy`, `Medium`, `Hard`, or `Any`)
  - Marks (single value like `2`, or a range like `1-3`, or `all`)
  - Or apply no filter and use all questions in the file.
- Choose how many questions to attempt in the session (enter a number, or `all`).
- Questions are randomly sampled (if you request fewer than available) or
  shuffled (when requesting all) so sessions vary.
- Flexible answer matching:
  - Case-insensitive normalization and removal of punctuation.
  - Detects option tokens such as `A`, `a)`, `1.`.
  - Accepts numeric answers written as words (e.g. `three` ↔ `3`).
  - Accepts short token containment (short correct tokens found in longer replies).
  - Conservative fuzzy matching for small typos (approx. threshold ≈ 88%).
- Saves per-topic performance to `performance.json`.
- Optionally uses `rapidfuzz` (if installed) for improved fuzzy matching.
- Clear performance: an explicit menu entry to permanently erase recorded stats
  with a confirmation step.

---

## Project structure

- `main-revision_quiz/`
  - `main-revision_quiz/main.py` - main CLI app and matching logic
  - `main-revision_quiz/questions/` - JSON question files (one file per level_subject)
  - `main-revision_quiz/performance.json` - created/updated at runtime
- `README.md` - this file

Run the program from the repository root:
```
python3 main-revision_quiz/main.py
```

---

## Question JSON format

Questions are plain JSON arrays. Each question is an object with these fields:

- `topic` (string) — topic name used when recording performance.
- `question` (string) — the text asked to the user.
- `answer` (string or array) — acceptable answer(s). Arrays list multiple acceptable forms.
- `marks` (integer) — integer marks value used by marks-based filtering.
- `difficulty` (string) — difficulty label (e.g. `Easy`, `Medium`, `Hard`).

Example:
```json
[
  {
    "topic": "Programming",
    "question": "What does IDE stand for?",
    "answer": "integrated development environment",
    "marks": 1,
    "difficulty": "Easy"
  },
  {
    "topic": "Computer Organization",
    "question": "What is instruction pipelining?",
    "answer": "overlapping stages of instruction execution to improve throughput",
    "marks": 3,
    "difficulty": "Hard"
  }
]
```

Notes about editing question files:
- Files are located in `main-revision_quiz/questions/` and are named `LEVEL_Subject.json`
  (for example: `GCSE_Computer_Science.json` or `ALevel_Biology.json`).
- Non-devs can edit these JSON files to add or adjust questions. Keep the JSON valid.
- Difficulty labels are detected from the contents; common labels are `Easy`, `Medium`, `Hard`.
  The program currently treats difficulty strings from the file as-is when presenting options.
  If you want case-insensitive matching, make sure to keep labels consistent (capitalised, e.g. `Hard`).

---

## How filters work

1. After choosing level and subject, you are asked how to filter:
   - `None` (no filter) — use all questions in that file.
   - `Difficulty` — you will get a menu of difficulties found in the file (`Any`, `Easy`, `Medium`, `Hard`, etc.).
     Choose `Any` to include every difficulty.
   - `Marks` — you can pick a single marks value shown in the file, or enter a custom value or range
     when prompted (supports `N` or `L-H` range).
2. After filters are applied, the program shows how many questions are available.
3. You choose how many questions to attempt:
   - Enter a number `1..N` or type `all` to use all available questions.
4. The program randomly samples/shuffles those questions and starts the session.

---

## Answer matching details (summary)

- Answers are normalized before comparison (unicode NFKC normalization, lowercasing,
  punctuation removed, repeated whitespace collapsed).
- Option token detection: a reply starting with `a)`, `A.`, `1.` or similar will be
  interpreted as the option token `a` / `1`.
- Numeric matching: both digits and common English word numbers (`three`, `twenty one`) are parsed.
- Containment: short correct answers (tokens) found inside a longer user reply are accepted.
- Fuzzy matching: if no exact/containment match, a conservative fuzzy similarity
  (≈88% threshold) is applied — optionally powered by `rapidfuzz` when available,
  otherwise Python's `difflib` is used.

---

## Performance tracking

- Per-topic performance is recorded to `main-revision_quiz/performance.json`.
- The format groups stats by `LEVEL_Subject` key and then by topic:
```json
{
  "GCSE_Computer_Science": {
    "Programming": { "attempted": 5, "correct": 4 },
    "Data Representation": { "attempted": 3, "correct": 2 }
  },
  "ALevel_Biology": {
    "Cell Structure": { "attempted": 2, "correct": 1 }
  }
}
```

- Use the "View Performance" option in the main menu to see a summary of recorded stats.

---

## Clearing recorded performance

There is a "Clear Performance" option in the main menu. Important details:
- The action permanently erases recorded statistics in `performance.json`.
- The CLI asks for explicit confirmation before deleting. By default the program uses a
  robust confirmation step to reduce accidental deletion.
- A cleared state writes an empty JSON object `{}` to `performance.json` so the program
  continues to work normally afterwards.
- If you want a backup before clearing, manually copy `main-revision_quiz/performance.json`.

---

## Dependencies & compatibility

- Python 3.8+ recommended.
- Optional: `rapidfuzz` — install with:
```
pip install rapidfuzz
```
  If `rapidfuzz` is not available, the program falls back to Python's `difflib` for fuzzy matching.

---

## UX: Example session flow

1. Run: `python3 main-revision_quiz/main.py`
2. Main menu:
   - 1. Start Quiz
   - 2. View Performance
   - 3. Clear Performance
   - 4. Exit
3. Start Quiz → choose level (GCSE / ALevel) → choose subject.
4. Choose filter: `None` / `Difficulty` / `Marks`.
   - If `Difficulty`, pick `Easy` / `Medium` / `Hard` or `Any`.
   - If `Marks`, enter a value (e.g., `2`), a range (`1-3`), or `all`.
5. Enter question count (e.g. `5` or `all`).
6. Answer questions in the terminal. Progress is saved.

---

## Use of AI

This project made limited, explicit use of the Zed AI agent available in the Zed IDE. The agent was used only to:

- Help format this README for easier reading and a consistent layout in the Markdown format.
- Generate question prompts / example questions to consider for the various subjects during authoring.

All suggestions from the Zed agent were reviewed, edited, and curated by the project author. The agent was not used to modify program logic, run code, or make automatic changes to the repository — its role was purely editorial and suggestive.
