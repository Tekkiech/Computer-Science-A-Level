import hashlib
import os
import sqlite3


class DatabaseManager:
    # This class handles all the SQL stuff. I put it in a separate class (OOP)
    # to make the main file less cluttered and get marks for encapsulation.
    def __init__(self, db_name="quiz_data.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._initialize_tables()

    def _initialize_tables(self):
        # Setting up my tables in 3rd Normal Form (3NF) to hit the AQA database requirements.
        # Everything is linked with Foreign Keys.
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                topic TEXT,
                question_text TEXT,
                answer_text TEXT,
                marks INTEGER,
                difficulty TEXT,
                FOREIGN KEY (subject_id) REFERENCES Subjects(id)
            );

            CREATE TABLE IF NOT EXISTS UserPerformance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                attempts INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                next_review_date TEXT,
                elo_rating INTEGER DEFAULT 1000,
                FOREIGN KEY (user_id) REFERENCES Users(id),
                FOREIGN KEY (question_id) REFERENCES Questions(id)
            );
        """)
        self.conn.commit()

    def create_user(self, username, password):
        # I'm using hashlib to hash passwords. My teacher said storing plain text
        # passwords is an instant fail for the security part of the NEA!
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute(
                "INSERT INTO Users (username, password_hash) VALUES (?, ?)",
                (username, hashed_pw),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # This triggers if the username is already taken (UNIQUE constraint)
            return False

    def verify_user(self, username, password):
        # Hash the password they typed and see if it matches the DB
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute(
            "SELECT id FROM Users WHERE username = ? AND password_hash = ?",
            (username, hashed_pw),
        )
        user = self.cursor.fetchone()
        return user[0] if user else None

    def close(self):
        self.conn.close()
