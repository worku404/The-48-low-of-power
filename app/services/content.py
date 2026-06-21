import json
import os
from flask import current_app

class ContentService:
    def __init__(self, data_path=None):
        self._data_path = data_path
        self._sections = None

    @property
    def data_path(self):
        if self._data_path is None:
            # Default path relative to project root
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self._data_path = os.path.join(root_dir, 'data', 'sections.json')
        return self._data_path

    def load_sections(self):
        """Loads and returns all sections from the JSON file."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Content database file not found at {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self._sections = json.load(f)
        return self._sections

    def get_all_sections(self):
        """Returns all sections. Loads if not already loaded."""
        if self._sections is None:
            self.load_sections()
        return self._sections

    def get_section(self, section_id):
        """Safely fetches a section by its ID (integer)."""
        try:
            section_id = int(section_id)
        except (ValueError, TypeError):
            return None
            
        sections = self.get_all_sections()
        for sec in sections:
            if sec['id'] == section_id:
                return sec
        return None
