"""
Content Agent Validators — Sprint 7.2
=======================================
Validates input parameter ranges and formatting constraints.
"""
from typing import List, Optional
from fastapi import HTTPException


def validate_generation_input(
    prompt: str,
    keywords: Optional[List[str]] = None,
    forbidden_words: Optional[List[str]] = None
) -> None:
    """Validate prompt limits and target boundaries."""
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise HTTPException(status_code=400, detail="Generation prompt cannot be empty.")
        
    if len(clean_prompt) < 10:
        raise HTTPException(status_code=400, detail="Generation prompt is too short. Please provide at least 10 characters.")
        
    if keywords:
        for kw in keywords:
            if not kw.strip():
                raise HTTPException(status_code=400, detail="SEO keywords list contains empty strings.")
                
    if forbidden_words:
        for word in forbidden_words:
            if not word.strip():
                raise HTTPException(status_code=400, detail="Forbidden words list contains empty strings.")
