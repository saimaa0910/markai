"""
Service Layer Data Transfer Objects.
"""

from dataclasses import dataclass


@dataclass
class ServiceBaseDTO:
    id: str
