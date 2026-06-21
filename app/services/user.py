from werkzeug.security import generate_password_hash, check_password_hash

class UserService:
    def __init__(self, db_service=None, db_path=None):
        if db_service is None:
            from app.services.db import DatabaseService
            db_service = DatabaseService(db_path=db_path)
        self.db_service = db_service

    def user_exists(self, username):
        """Returns True if the username exists in the users table."""
        if not username:
            return False
        cursor = self.db_service.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username.strip(),)
        )
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    def create_user(self, username, password):
        """Creates a new user with a hashed password. Returns True if successful."""
        if not username or not password:
            return False
        hashed_password = generate_password_hash(password)
        try:
            cursor = self.db_service.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username.strip(), hashed_password)
            )
            cursor.close()
            self.db_service.commit()
            return True
        except Exception:
            self.db_service.rollback()
            return False

    def verify_user(self, username, password):
        """Verifies if the credentials are correct. Returns True if verified."""
        if not username or not password:
            return False
        cursor = self.db_service.execute(
            "SELECT password FROM users WHERE username = ?",
            (username.strip(),)
        )
        row = cursor.fetchone()
        cursor.close()
        if row and check_password_hash(row['password'], password):
            return True
        return False

    def get_progress(self, username):
        """Fetches the list of completed law IDs for the user."""
        if not username:
            return []
        cursor = self.db_service.execute(
            "SELECT law_id FROM user_progress WHERE username = ? AND completed = 1",
            (username.strip(),)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [row['law_id'] for row in rows]

    def save_progress(self, username, law_id, completed=True):
        """Saves or updates the progress of a specific law for the user."""
        if not username:
            return False
        completed_val = 1 if completed else 0
        try:
            if self.db_service.is_postgres():
                # PostgreSQL-compatible upsert syntax using EXCLUDED values
                cursor = self.db_service.execute("""
                    INSERT INTO user_progress (username, law_id, completed, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(username, law_id) DO UPDATE SET completed = EXCLUDED.completed, updated_at = CURRENT_TIMESTAMP
                """, (username.strip(), law_id, completed_val))
            else:
                # SQLite upsert syntax
                cursor = self.db_service.execute("""
                    INSERT INTO user_progress (username, law_id, completed, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(username, law_id) DO UPDATE SET completed = ?, updated_at = CURRENT_TIMESTAMP
                """, (username.strip(), law_id, completed_val, completed_val))
            cursor.close()
            self.db_service.commit()
            return True
        except Exception:
            self.db_service.rollback()
            return False
