"""
Knowledge Domain Unit Tests.
"""

from api.domain.knowledge.validator import validate_doc_title


def test_doc_title_validation():
    assert validate_doc_title("Architecture Guide") is True
    assert validate_doc_title("   ") is False
