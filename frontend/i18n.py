import json
from pathlib import Path
from typing import Optional, Dict, Any


class I18nService:
    def __init__(self, locales_file: str = None, default_lang: str = "ko"):
        if locales_file is None:
            locales_file = Path(__file__).parent.parent / "frontend" / "locales.json"

        with open(locales_file, "r", encoding="utf-8") as f:
            self.translations = json.load(f)

        self.default_lang = default_lang
        self.current_lang = default_lang
        self.available_languages = list(self.translations.keys())

    def set_language(self, lang: str):
        if lang in self.available_languages:
            self.current_lang = lang
        else:
            self.current_lang = self.default_lang

    def get_language(self) -> str:
        return self.current_lang

    def get_available_languages(self) -> list:
        return self.available_languages

    def translate(self, key: str, **kwargs) -> str:
        keys = key.split(".")
        value = self.translations.get(self.current_lang, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                break

        if value is None:
            return key

        if isinstance(value, str):
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value

        return key

    def t(self, key: str, **kwargs) -> str:
        return self.translate(key, **kwargs)


i18n = I18nService()
