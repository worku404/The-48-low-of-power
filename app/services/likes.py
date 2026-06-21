import sqlite3
import os
from flask import g

class LikesService:
    def __init__(self, db_path=None):
        self._db_path = db_path

    @property
    def db_path(self):
        if self._db_path is None:
            from flask import current_app
            self._db_path = os.path.join(current_app.instance_path, 'likes.sqlite3')
        return self._db_path

    def get_db(self):
        if 'db' not in g:
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)
            g.db = sqlite3.connect(self.db_path)
            g.db.row_factory = sqlite3.Row
            self._init_db(g.db)
        return g.db

    def _init_db(self, db):
        db.execute("""
            CREATE TABLE IF NOT EXISTS section_likes (
                section_id INTEGER PRIMARY KEY,
                like_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS visitor_likes (
                visitor_cookie TEXT NOT NULL,
                section_id INTEGER NOT NULL,
                PRIMARY KEY (visitor_cookie, section_id)
            )
        """)
        db.commit()

    def get_likes(self, section_id):
        db = self.get_db()
        cursor = db.execute(
            "SELECT like_count FROM section_likes WHERE section_id = ?",
            (section_id,)
        )
        row = cursor.fetchone()
        return row['like_count'] if row else 0

    def has_liked(self, visitor_cookie, section_id):
        if not visitor_cookie:
            return False
        db = self.get_db()
        cursor = db.execute(
            "SELECT 1 FROM visitor_likes WHERE visitor_cookie = ? AND section_id = ?",
            (visitor_cookie, section_id)
        )
        return cursor.fetchone() is not None

    def add_like(self, visitor_cookie, section_id):
        if not visitor_cookie:
            return self.get_likes(section_id), False

        db = self.get_db()
        
        # Check if already liked
        if self.has_liked(visitor_cookie, section_id):
            return self.get_likes(section_id), False

        try:
            # Insert visitor record
            db.execute(
                "INSERT INTO visitor_likes (visitor_cookie, section_id) VALUES (?, ?)",
                (visitor_cookie, section_id)
            )
            
            # Upsert like count
            db.execute("""
                INSERT INTO section_likes (section_id, like_count)
                VALUES (?, 1)
                ON CONFLICT(section_id) DO UPDATE SET like_count = like_count + 1
            """, (section_id,))
            
            db.commit()
            return self.get_likes(section_id), True
        except sqlite3.IntegrityError:
            db.rollback()
            return self.get_likes(section_id), False

    @staticmethod
    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()
