import os
import tempfile
import pytest
import json
from app import create_app

@pytest.fixture
def temp_db_file():
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def temp_cache_dir():
    with tempfile.TemporaryDirectory() as cache_dir:
        yield cache_dir

@pytest.fixture
def mock_sections_file():
    # Helper to generate a mock sections file containing 48 elements for testing
    sections = []
    # Seed Law 1 and Law 2
    sections.append({
        "id": 1,
        "label": "Law 1",
        "title": "የሙከራ ርዕስ 1",
        "body": "የሙከራ ይዘት እዚህ ይገኛል::",
        "language": "am"
    })
    sections.append({
        "id": 2,
        "label": "Law 2",
        "title": "የሙከራ ርዕስ 2",
        "body": "ሁለተኛው የሙከራ ይዘት::",
        "language": "am"
    })
    for i in range(3, 49):
        sections.append({
            "id": i,
            "label": f"Law {i}",
            "title": "",
            "body": "",
            "language": "am"
        })
        
    fd, path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)
        
    yield path
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def app(temp_db_file, temp_cache_dir, mock_sections_file):
    # Initialize the app with test configs overriding standard instance folders
    app = create_app({
        'TESTING': True,
        'DATABASE_PATH': temp_db_file,
        'AUDIO_CACHE_DIR': temp_cache_dir,
        'CONTENT_JSON_PATH': mock_sections_file,
        'SECRET_KEY': 'test-secret-key'
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()
