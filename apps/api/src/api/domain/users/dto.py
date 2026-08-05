"""
Users Domain Data Transfer Objects.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserDTO:
    id: str
    email: str
    full_name: Optional[str] = None
