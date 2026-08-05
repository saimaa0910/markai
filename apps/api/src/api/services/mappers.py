"""
Service Layer Data Mappers.
"""

from typing import Dict, Any


def map_service_response(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}
