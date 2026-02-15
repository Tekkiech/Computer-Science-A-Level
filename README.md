# Adaptive Revision & Quiz System — A‑Level Computer Science Project

This repository contains an interactive, terminal-based revision and quiz system developed as an A‑Level Computer Science project. It is written in Python and demonstrates practical software engineering: requirement-driven design, input normalisation, configurable fuzzy matching, simple persistence and user-focused behaviour appropriate for a revision tool.

This README is written specifically for the A‑Level context: it explains the project's aim, methodology, key design decisions, how to run and test the system, evaluation of strengths and limitations, and suggested future work for extension or improvement.

---

## Aim (Project Purpose)

- Provide a lightweight CLI application students can use to rehearse GCSE and A‑Level topics.
- Demonstrate the application of software engineering concepts required for A‑Level coursework:
  - Requirements capture and prioritisation
  - Modular code with clear responsibilities
  - Input normalisation and tolerant answer matching
  - Persistent recording of per-topic performance
  - Clear documentation and testable behaviour

---

## Scope & Features

- Level/subject selection (GCSE / ALevel across multiple subjects).
- Questions stored as per-subject JSON files so the data is editable without code changes.
- Flexible answer matching that tolerates:
  - capitalization and punctuation differences
  - small spelling mistakes (fuzzy matching)
  - numbers written as words or digits (e.g. `three` ↔ `3`)
  - multiple correct answer variants (synonyms)
  - option-style tokens (e.g. `A`, `a.`, `a)`)
- Per-topic performance tracking saved to `performance.json`.
- Optional use of `rapidfuzz` for improved fuzzy matching (still works without it via `difflib`).

---

## Project structure (important files & folders)

- `main-revision_quiz/`
  - `main-revision_quiz/main.py` — main program, CLI and matching logic
  - `main-revision_quiz/questions/` — JSON question banks, one file per level/subject
  - `main-revision_quiz/performance.json` — created at runtime to persist progress
- `README.md` — this file
- `.gitignore` — configured for macOS system files

Example question file (one of the JSON banks):

```Computer-Science-A-Level-Project/main-revision_quiz/questions/GCSE_Computer_Science.json#L1-40
[
  {
    "topic": "Programming",
    "question": "What does IDE stand for?",
    "answer": "integrated development environment",
    "marks": 1,
    "difficulty": "Easy"
  },
  {
    "topic": "Data Representation",
    "question": "How many bits are in a byte?",
    "answer": "8",
    "marks": 1,
    "difficulty": "Easy"
  }
  ...
]
```

(See `main-revision_quiz/questions/` for all subject files.)

---

## Methodology (how the project was developed)

1. Requirements
   - Identify needs for a revision tool (simple UI, configurable content, tolerant matching).
   - Prioritise reliability and explainability for an A‑Level demonstration over ambitious scope.

2. Design
   - Keep the application single-threaded, simple CLI to make it demonstrable and easy to grade.
   - Store questions in JSON so non-technical users (teachers/students) can edit content.
   - Implement matching inside the quiz flow to keep the example self-contained for marking.

3. Implementation
   - Python 3; limited external dependencies.
   - Answer matching uses layered approach (normalisation → deterministic option matching → numeric handling → substring → fuzzy).
   - Performance saved as JSON with a clear structure to inspect manually.

4. Testing (see Testing section below)
   - Manual play-through to check typical variants and edge-cases (capitalisation, option formats).
   - Where applicable, unit tests are recommended; examples are suggested in the Testing section.

---

## Design decisions and justifications

- CLI app (not GUI): Easier to explain, lightweight for coursework, and focuses attention on core logic.
- JSON data files: separates data and code, enabling lesson content editing without code changes.
- Layered matching: prioritises deterministic, explainable checks (exact/option/numeric) before fuzzy matching; this reduces false positives while still being forgiving.
- Optional `rapidfuzz`: improves fuzzy matching quality if available, but the program works without it (fallback to `difflib`) — this keeps the project accessible to examiners without special installs.
- Simplicity over optimisation: the app holds question banks in memory and iterates sequentially (sufficient for small banks and coursework requirements).

---

## How answer matching works (concise)

1. Normalise input (Unicode NFKC, lower-case, remove punctuation, collapse whitespace).
2. Detect option tokens (`A`, `b)`, `1.` normalized to `a`, `b`, `1`).
3. Numeric parsing — accept `3`, `3.0` and `three` as equivalent when both sides are numeric.
4. Containment check for short canonical tokens inside longer responses.
5. Fuzzy matching (conservative threshold by default — ~88%). Uses `rapidfuzz` if installed otherwise `difflib`.

This layered approach is documented in code and intended to be explainable for an A‑Level project write-up.

---

## Running the application

Requirements:
- Python 3.8+ (recommended)
- Optional: `rapidfuzz` for better fuzzy matching

Run from the repository root:

```/dev/null/usage.md#L1-3
# From the repository root:
python3 main-revision_quiz/main.py
```

Optional: install the fuzzy-match enhancement:

```/dev/null/usage.md#L4-5
pip install rapidfuzz
```

During run:
- Follow the numbered menus to choose level and subject.
- Answer questions via typing; acceptable variants are handled by the matcher.
- At the end of a session the program saves updated performance to `performance.json`.

---

## Testing and validation

For an A‑Level project, you should demonstrate testing in two ways:

1. Manual test cases (required in viva/portfolio)
   - Examples to manually verify:
     - Exact answer matching: correct canonical string.
     - Option tokens: `A`, `a)`, `a.` all accepted for a stored `"A"`.
     - Numeric variants: `three`, `3`, `3.0` accepted when answer is numeric.
     - Fuzzy acceptance: a small typo like `integreted development environment` still accepted (depending on fuzzy threshold).
     - Incorrect rejection: intentionally wrong answers should be rejected.

2. Automated tests (recommended for higher marks)
   - Extract matching helpers into a module and write unit tests using `pytest`.
   - Sample test cases should cover:
     - Normalisation function behaviour (quotes, punctuation, whitespace)
     - Option extraction
     - Word-number parsing
     - Numeric tolerance checks
     - Fuzzy acceptance vs rejection at boundary thresholds

Example of tests to add (pseudo/descriptor; add to `tests/` when implementing):

- `test_normalize_text`: inputs with punctuation & unicode quotes → expected normalized output.
- `test_option_normalize`: `A.`, `a)`, `A` → `"a"`.
- `test_word_number_to_int`: `"twenty one"` → `21`.
- `test_fuzzy_threshold`: verify a near-miss is accepted above threshold and rejected below.

---

## Evaluation (strengths and limitations)

Strengths:
- Clear, explainable code suitable for a coursework submission and viva.
- Flexible answer matching lowers friction for revision.
- Easy content editing via JSON.

Limitations:
- Not strict enough for automated high-stakes marking — fuzzy matching can introduce false positives for very short answers unless threshold tightened.
- No authentication, user accounts or multi-user support (out of scope for A‑Level project).
- Currently CLI-only; user experience could be improved with a basic web or GUI front-end.
- No formal automated tests included by default — adding them improves maintainability and demonstrability.

---

## Future work / extension ideas (good topics for further development or higher marks)

- Extract matching logic into `main-revision_quiz/match_utils.py` and add a comprehensive test-suite using `pytest`.
- Per-question configuration: `strict` flag (exact-only), `numeric_tolerance`, or `fuzzy_threshold`.
- Web interface (simple Flask or FastAPI front-end) for classroom use and user accounts.
- Import/Export tools for question banks (CSV ↔ JSON) to simplify content creation.
- Add spaced-repetition or item scheduling to make the revision adaptive rather than static.
- Add logging of near-misses (answers close to threshold) to refine question wording and thresholds.

---

## Submission notes (for your coursework folder / write-up)

When preparing your A‑Level project report or submission:
- Describe the layered matching algorithm (rationale and examples).
- Include sample manual test cases and one or two automated unit tests if implemented.
- Discuss design trade-offs (e.g., user convenience vs marking strictness).
- Mention optional dependency `rapidfuzz` and why it's optional.
- Provide a short demonstration script (e.g., sample session transcript) and a brief evaluation.

---

## Contact & support

If you'd like:
- I can extract the matching helpers into a separate module and provide unit tests and example test cases.
- I can create a short HOWTO file describing the steps you should include in your coursework folder (test results, design notes, screenshots/transcripts).

Good luck with your A‑Level project demonstration — this repository is structured and documented so you can explain both the implementation and the reasoning behind your design choices.
