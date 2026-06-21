import pytest
from app.services.content import ContentService

def test_load_all_sections(app):
    # Verify content loading service successfully loads exactly 48 sections
    with app.app_context():
        service = app.content_service
        sections = service.get_all_sections()
        assert len(sections) == 48

def test_first_sections_seeded(app):
    # Check that Law 1 and Law 2 contain our seed content
    with app.app_context():
        service = app.content_service
        law1 = service.get_section(1)
        assert law1 is not None
        assert law1['label'] == "Law 1"
        assert len(law1['body']) > 0

        law2 = service.get_section(2)
        assert law2 is not None
        assert law2['label'] == "Law 2"
        assert len(law2['body']) > 0

def test_untranslated_sections_empty(app):
    # Verify that laws 3-48 contain empty body values ("Coming soon" state)
    with app.app_context():
        service = app.content_service
        for i in range(3, 49):
            section = service.get_section(i)
            assert section is not None
            assert section['body'] == ""
            assert section['title'] == ""

def test_invalid_section_lookups(app):
    # Check that out of bounds IDs or invalid strings return None
    with app.app_context():
        service = app.content_service
        assert service.get_section(0) is None
        assert service.get_section(49) is None
        assert service.get_section("invalid") is None
        assert service.get_section(None) is None
