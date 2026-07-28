"""
EAIMOS Knowledge Base Validators
=================================
Validation rules for chunk overlap and collection visibility.
"""

from api.services.base.service_exceptions import ValidationError
from api.services.knowledge.constants import SUPPORTED_KNOWLEDGE_VISIBILITIES


def validate_chunk_overlap(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_overlap >= chunk_size:
        raise ValidationError(
            message="Chunk overlap must be strictly smaller than chunk size.",
            field_errors=[{"field": "chunk_overlap", "message": f"Overlap ({chunk_overlap}) >= Size ({chunk_size})"}],
        )


def validate_visibility_supported(visibility: str) -> None:
    if visibility.upper() not in SUPPORTED_KNOWLEDGE_VISIBILITIES:
        raise ValidationError(
            message=f"Unsupported visibility '{visibility}'.",
            field_errors=[{"field": "visibility", "message": f"Supported visibilities: {sorted(SUPPORTED_KNOWLEDGE_VISIBILITIES)}"}],
        )
