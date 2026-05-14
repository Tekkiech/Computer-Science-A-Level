import json
import os
import sqlite3


def migrate_data(db_path, questions_dir):
    print(f"Migrating data from {questions_dir} to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing data so we don't duplicate if run multiple times
    cursor.execute("DELETE FROM Questions")
    cursor.execute("DELETE FROM Subjects")

    for filename in os.listdir(questions_dir):
        if filename.endswith(".json"):
            parts = filename.replace(".json", "").split("_", 1)
            if len(parts) < 2:
                continue
            level = parts[0]
            subject_name = parts[1].replace("_", " ")

            cursor.execute(
                "INSERT INTO Subjects (level, name) VALUES (?, ?)",
                (level, subject_name),
            )
            subject_id = cursor.lastrowid

            filepath = os.path.join(questions_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                questions = json.load(f)
                for q in questions:
                    ans = q["answer"]
                    if isinstance(ans, list):
                        ans = json.dumps(ans)  # Store arrays as JSON strings in the DB

                    cursor.execute(
                        """
                        INSERT INTO Questions (subject_id, topic, question_text, answer_text, marks, difficulty)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            subject_id,
                            q.get("topic", "General"),
                            q.get("question", ""),
                            ans,
                            q.get("marks", 1),
                            q.get("difficulty", "Medium"),
                        ),
                    )

    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    # Use absolute paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "quiz_data.db")
    questions_dir = os.path.join(script_dir, "..", "questions")
    migrate_data(db_path, questions_dir)
