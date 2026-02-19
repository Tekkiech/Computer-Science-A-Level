# Adaptive Revision & Quiz System - A-Level Computer Science Project

Simple CLI quiz tool in Python. Use it to practice GCSE and A-Level topics.  
Shows clear code, basic persistence, and tolerant answer matching.

## Aim
- Lightweight revision app students can use.
- Show software engineering ideas for coursework.
- Keep code easy to explain in a viva.

## Quick features
- Choose level and subject.
- Questions stored as JSON so non-devs can edit them.
- Flexible answer matching: case, punctuation, small typos.
- Accepts numbers as words or digits (e.g. `three` and `3`).
- Saves per-topic performance to `performance.json`.
- Optional `rapidfuzz` for better fuzzy matching.

## Project structure
- `main-revision_quiz/`
  - `main-revision_quiz/main.py` - main app and matching logic
  - `main-revision_quiz/questions/` - JSON question files
  - `main-revision_quiz/performance.json` - created at runtime
- `README.md` - this file
- `.gitignore`

Example question file:
```Computer-Science-A-Level-Project/main-revision_quiz/questions/GCSE_Computer_Science.json#L1-14
[
  {
    "topic": "Programming",
    "question": "What does IDE stand for?",
    "answer": "integrated development environment",
    "marks": 1,
    "difficulty": "Easy"
  }
]
```

## How it was built (short)
1. Picked simple CLI so it's easy to demo and grade.  
2. Questions in JSON to separate data and code.  
3. Matching uses a few rules in order, then fuzzy match.  
4. Minimal dependencies so it runs on most systems.

## Design notes
- CLI only to stay small and explainable.  
- Layered matching to avoid false positives.  
- `rapidfuzz` is optional. Works fine with Python built-ins.  
- Keeps everything in memory for simplicity.

## How answer matching works
1. Normalize text (lowercase, remove weird quotes and punctuation).  
2. Detect option tokens like `A`, `a)`, `1.`.  
3. Parse numbers: accept `three`, `3`, `3.0`.  
4. Allow short correct tokens inside longer replies.  
5. Conservative fuzzy match for small typos (default threshold ~88%).

## Run it
Requirements:
- Python 3.8+  
- Optional: `pip install rapidfuzz`

Run:
```/dev/null/usage.md#L1-3
python3 main-revision_quiz/main.py
```

Follow the menus and answer questions in the terminal. Progress is saved to `performance.json`.
