"""
Auth Domain Entity & DTO Mappers.
"""

from typing import Dict, Any
from .dto import AuthUserDTO


def map_dict_to_auth_user_dto(data: Dict[str, Any]) -> AuthUserDTO:
    return AuthUserDTO(
        id=data.get("id", ""),
        email=data.get("email", ""),
        roles=data.get("roles", []),
    )
