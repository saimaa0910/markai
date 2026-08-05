"""
Auth Domain Data Transfer Objects (DTOs).
"""

from dataclasses import dataclass


@dataclass
class AuthUserDTO:
    id: str
    email: str
    roles: list[str]
