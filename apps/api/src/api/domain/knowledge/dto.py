"""
Knowledge DTO.
"""

from dataclasses import dataclass


@dataclass
class DocumentDTO:
    id: str
    title: str
