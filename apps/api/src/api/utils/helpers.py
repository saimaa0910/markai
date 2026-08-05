"""
Backend General Utility & Helper Functions.
"""

from typing import Any, Dict
import json


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values and sanitize dictionary payloads.
    """
    return {k: v for k, v in data.items() if v is not None}
