"""
EAIMOS AI Gateway Validators
==============================
Validation rules for prompt syntax, token budgets, AI providers, and vector parameters.
"""

import re
from typing import List, Set
from api.services.base.service_exceptions import ValidationError, BusinessRuleViolation
from api.services.ai.constants import SUPPORTED_AI_PROVIDERS, PROMPT_VAR_REGEX


def validate_model_provider_supported(provider: str) -> None:
    if provider.lower() not in SUPPORTED_AI_PROVIDERS:
        raise ValidationError(
            message=f"Unsupported AI provider '{provider}'.",
            field_errors=[{"field": "provider", "message": f"Supported providers: {sorted(SUPPORTED_AI_PROVIDERS)}"}],
        )


def extract_prompt_variables(template_text: str) -> List[str]:
    """Extract all {{var_name}} instances from a prompt template string."""
    matches = re.findall(PROMPT_VAR_REGEX, template_text)
    # Deduplicate preserving order
    seen: Set[str] = set()
    result: List[str] = []
    for var in matches:
        if var not in seen:
            seen.add(var)
            result.append(var)
    return result


def validate_prompt_template_syntax(template_text: str) -> List[str]:
    """Check for malformed braces in template."""
    # Simple syntax check for unclosed {{ or }}
    open_count = template_text.count("{{")
    close_count = template_text.count("}}")
    if open_count != close_count:
        raise ValidationError(
            message="Malformed prompt template syntax: unbalanced '{{' and '}}' delimiters.",
            field_errors=[{"field": "template", "message": f"Found {open_count} '{{{{' and {close_count} '}}}}'."}],
        )
    return extract_prompt_variables(template_text)


def validate_chunk_size_and_overlap(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_overlap >= chunk_size:
        raise ValidationError(
            message="Chunk overlap must be strictly less than chunk size.",
            field_errors=[{"field": "chunk_overlap", "message": f"Overlap ({chunk_overlap}) >= Size ({chunk_size})"}],
        )
