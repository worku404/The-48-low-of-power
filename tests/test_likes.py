import pytest
import sqlite3
from app.services.likes import LikesService

def test_initial_likes_is_zero(app):
    with app.app_context():
        service = app.likes_service
        assert service.get_likes(1) == 0

def test_add_like_success(app):
    with app.app_context():
        service = app.likes_service
        visitor = "visitor-uuid-123"
        
        # Like first time
        likes, success = service.add_like(visitor, 1)
        assert success is True
        assert likes == 1
        assert service.get_likes(1) == 1
        assert service.has_liked(visitor, 1) is True

def test_prevent_double_like(app):
    with app.app_context():
        service = app.likes_service
        visitor = "visitor-uuid-123"
        
        # First like
        service.add_like(visitor, 1)
        # Second like attempt from same visitor
        likes, success = service.add_like(visitor, 1)
        
        assert success is False
        assert likes == 1
        assert service.get_likes(1) == 1

def test_multiple_visitors_increment(app):
    with app.app_context():
        service = app.likes_service
        
        service.add_like("visitor-A", 1)
        service.add_like("visitor-B", 1)
        likes, success = service.add_like("visitor-C", 1)
        
        assert success is True
        assert likes == 3
        assert service.get_likes(1) == 3

def test_persistence_on_database_restart(app):
    # Retrieve DB file path
    db_path = app.config['DATABASE_PATH']
    visitor = "persisting-visitor"
    
    # Write a like
    with app.app_context():
        service = app.likes_service
        service.add_like(visitor, 5)
        assert service.get_likes(5) == 1
        
    # Reinitialize a new service pointing to the same file (simulates app restart)
    new_service = LikesService(db_path=db_path)
    with app.app_context():
        # Read from the file
        assert new_service.get_likes(5) == 1
        assert new_service.has_liked(visitor, 5) is True
