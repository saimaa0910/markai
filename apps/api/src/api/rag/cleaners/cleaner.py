"""
Text Cleaner & Normalizer.
"""


class TextCleaner:
    def clean(self, raw_text: str) -> str:
        # TODO: Normalize whitespace and remove control characters
        return raw_text.strip()


text_cleaner = TextCleaner()
