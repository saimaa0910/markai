"""
Knowledge Validators.
"""


def validate_doc_title(title: str) -> bool:
    return len(title.trim()) > 0 if hasattr(title, 'trim') else len(title.strip()) > 0
