"""
Knowledge Permissions.
"""

from enum import Enum


class KnowledgePermission(str, Enum):
    READ = "knowledge:read"
    WRITE = "knowledge:write"
    DELETE = "knowledge:delete"
