"""
Knowledge Model Entity.
"""

from pydantic import BaseModel


class DocumentDomainEntity(BaseModel):
    id: str
    title: str
    file_path: str
