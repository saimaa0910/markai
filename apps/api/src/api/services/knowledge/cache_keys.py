"""
EAIMOS Knowledge Cache Keys
============================
Cache key functions for Knowledge Base & Vector Indexing Services.
"""

from typing import Union
import uuid

KNOWLEDGE_CACHE_PREFIX: str = "knowledge"


def collection_cache_key(collection_id: Union[uuid.UUID, str]) -> str:
    return f"{KNOWLEDGE_CACHE_PREFIX}:col:{str(collection_id)}"


def document_cache_key(doc_id: Union[uuid.UUID, str]) -> str:
    return f"{KNOWLEDGE_CACHE_PREFIX}:doc:{str(doc_id)}"
