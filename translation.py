import json
import os
from aqt import mw


class Translator:
    def __init__(self):
        # Get language from Anki (e.g. "pl_PL", "pt_PT")

        full_code = mw.pm.meta.get("defaultLang", "en") or "en"
        if full_code is None:
            full_code = "en"

        # Cut lang code (e.g.: pl_PL to pl)
        self.lang_code = full_code.split('_')[0]

        self.translations = {}
        self.load_translations()

    def load_translations(self):
        base_dir = os.path.dirname(__file__)
        i18n_dir = os.path.join(base_dir, "i18n")

        # First load English as base
        en_path = os.path.join(i18n_dir, "en.json")
        if os.path.exists(en_path):
            with open(en_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)

        # If user language is not English then load it and overwrite
        if self.lang_code != "en":
            lang_path = os.path.join(i18n_dir, f"{self.lang_code}.json")
            if os.path.exists(lang_path):
                with open(lang_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                    # Actualize vocabulary (overwrite keys)
                    self.translations.update(local_data)

    def tr(self, key: str, **kwargs) -> str:
        # return translated text for selected key
        # handle formatting variable, ex. {count}
        # Get text, if there is no key - return key itself
        text = self.translations.get(key, key)

        # Handle dynamic formating (ex. insert numbers)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text


# Create one, global instance
manager = Translator()


# Short global function for convenience (same like in Qt tr())
def tr(key: str, **kwargs) -> str:
    return manager.tr(key, **kwargs)
