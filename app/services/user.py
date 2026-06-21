import sqlite3
import os
from flask import g, current_app
from werkzeug.security import generate_password_hash, check_password_hash

class UserService:
    def __init__(self, db_path=None):
        self._db_path = db_path

    @property
    def db_path(self):
        if self._db_path is None:
            self._db_path = os.path.join(current_app.instance_path, 'likes.sqlite3')
        return self._db_path

    def get_db(self):
        if 'db' not in g:
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)
            g.db = sqlite3.connect(self.db_path)
            g.db.row_factory = sqlite3.Row
        return g.db

    def user_exists(self, username):
        """Returns True if the username exists in the users table."""
        if not username:
            return False
        db = self.get_db()
        cursor = db.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username.strip(),)
        )
        return cursor.fetchone() is not None

    def create_user(self, username, password):
        """Creates a new user with a hashed password. Returns True if successful."""
        if not username or not password:
            return False
        db = self.get_db()
        hashed_password = generate_password_hash(password)
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username.strip(), hashed_password)
            )
            db.commit()
            return True
        except sqlite3.IntegrityError:
            db.rollback()
            return False

    def verify_user(self, username, password):
        """Verifies if the credentials are correct. Returns True if verified."""
        if not username or not password:
            return False
        db = self.get_db()
        cursor = db.execute(
            "SELECT password FROM users WHERE username = ?",
            (username.strip(),)
        )
        row = cursor.fetchone()
        if row and check_password_hash(row['password'], password):
            return True
        return False

    def get_progress(self, username):
        """Fetches the list of completed law IDs for the user."""
        if not username:
            return []
        db = self.get_db()
        cursor = db.execute(
            "SELECT law_id FROM user_progress WHERE username = ? AND completed = 1",
            (username.strip(),)
        )
        return [row['law_id'] for row in cursor.fetchall()]

    def save_progress(self, username, law_id, completed=True):
        """Saves or updates the progress of a specific law for the user."""
        if not username:
            return False
        db = self.get_db()
        completed_val = 1 if completed else 0
        try:
            db.execute("""
                INSERT INTO user_progress (username, law_id, completed, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(username, law_id) DO UPDATE SET completed = ?, updated_at = CURRENT_TIMESTAMP
            """, (username.strip(), law_id, completed_val, completed_val))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
