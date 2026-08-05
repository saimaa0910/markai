"""
Knowledge Events.
"""

from dataclasses import dataclass


@dataclass
class DocumentIngestedEvent:
    doc_id: str
    title: str
