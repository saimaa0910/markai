"""
EAIMOS Knowledge Base Constants
================================
Constants for Sprint 8 Knowledge Base, Document Ingestion & Vector Indexing Services.
"""

from typing import Set

SUPPORTED_KNOWLEDGE_VISIBILITIES: Set[str] = {"ORGANIZATION", "TEAM", "PRIVATE", "PUBLIC"}
SUPPORTED_PROCESSING_STATUSES: Set[str] = {"PENDING", "EXTRACTING", "CHUNKING", "EMBEDDING", "INDEXED", "FAILED"}
SUPPORTED_CHUNKING_STRATEGIES: Set[str] = {"FIXED_SIZE", "SEMANTIC_PARAGRAPH", "MARKDOWN_HEADER"}

DEFAULT_CHUNK_SIZE: int = 512
DEFAULT_CHUNK_OVERLAP: int = 64
MAX_DOCUMENT_SIZE_BYTES: int = 52_428_800  # 50 MB
