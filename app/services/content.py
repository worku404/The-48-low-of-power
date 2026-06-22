import json
import os
from flask import current_app

class ContentService:
    def __init__(self, data_path=None, data_path_en=None):
        self._data_path = data_path
        self._data_path_en = data_path_en
        self._sections = None
        self._sections_en = None

    @property
    def data_path(self):
        if self._data_path is None:
            # Default path relative to project root
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self._data_path = os.path.join(root_dir, 'data', 'sections.json')
        return self._data_path

    @property
    def data_path_en(self):
        if self._data_path_en is None:
            # Default path relative to project root
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self._data_path_en = os.path.join(root_dir, 'data', 'sections_en.json')
        return self._data_path_en

    def load_sections(self, lang='am'):
        """Loads and returns all sections from the JSON file for the specified language."""
        if lang == 'en':
            if not os.path.exists(self.data_path_en):
                raise FileNotFoundError(f"English content database file not found at {self.data_path_en}")
            with open(self.data_path_en, 'r', encoding='utf-8') as f:
                self._sections_en = json.load(f)
            return self._sections_en
        else:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"Content database file not found at {self.data_path}")
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self._sections = json.load(f)
            return self._sections

    def get_all_sections(self, lang='am'):
        """Returns all sections for a language. Loads if not already loaded."""
        if lang == 'en':
            if self._sections_en is None:
                self.load_sections(lang='en')
            return self._sections_en
        else:
            if self._sections is None:
                self.load_sections(lang='am')
            return self._sections

    def get_section(self, section_id, lang='am'):
        """Safely fetches a section by its ID (integer) and language."""
        try:
            section_id = int(section_id)
        except (ValueError, TypeError):
            return None
            
        sections = self.get_all_sections(lang)
        for sec in sections:
            if sec['id'] == section_id:
                return sec
        return None
