class LikesService:
    def __init__(self, db_service=None, db_path=None):
        if db_service is None:
            from app.services.db import DatabaseService
            db_service = DatabaseService(db_path=db_path)
        self.db_service = db_service

    def get_likes(self, section_id):
        cursor = self.db_service.execute(
            "SELECT like_count FROM section_likes WHERE section_id = ?",
            (section_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row['like_count'] if row else 0

    def has_liked(self, visitor_cookie, section_id):
        if not visitor_cookie:
            return False
        cursor = self.db_service.execute(
            "SELECT 1 FROM visitor_likes WHERE visitor_cookie = ? AND section_id = ?",
            (visitor_cookie, section_id)
        )
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    def add_like(self, visitor_cookie, section_id):
        if not visitor_cookie:
            return self.get_likes(section_id), False

        # Check if already liked
        if self.has_liked(visitor_cookie, section_id):
            return self.get_likes(section_id), False

        try:
            # Insert visitor record
            cursor_vis = self.db_service.execute(
                "INSERT INTO visitor_likes (visitor_cookie, section_id) VALUES (?, ?)",
                (visitor_cookie, section_id)
            )
            cursor_vis.close()
            
            # Upsert like count
            if self.db_service.is_postgres():
                cursor_like = self.db_service.execute("""
                    INSERT INTO section_likes (section_id, like_count)
                    VALUES (?, 1)
                    ON CONFLICT(section_id) DO UPDATE SET like_count = section_likes.like_count + 1
                """, (section_id,))
            else:
                cursor_like = self.db_service.execute("""
                    INSERT INTO section_likes (section_id, like_count)
                    VALUES (?, 1)
                    ON CONFLICT(section_id) DO UPDATE SET like_count = like_count + 1
                """, (section_id,))
            cursor_like.close()
            
            self.db_service.commit()
            return self.get_likes(section_id), True
        except Exception:
            self.db_service.rollback()
            return self.get_likes(section_id), False
