from typing import Any, Dict
from fastapi import HTTPException, status
from api.ai.agents.image.constants import ASPECT_RATIOS, STYLE_LIBRARY, SUPPORTED_MODELS


def validate_aspect_ratio(ratio: str) -> bool:
    """Check if ratio is supported."""
    return ratio in ASPECT_RATIOS


def validate_style(style: str) -> bool:
    """Check if style is in library."""
    return style.lower() in STYLE_LIBRARY


def validate_image_generation_request(payload: Dict[str, Any]) -> None:
    """Validate all payload parameters for image generation tasks."""
    prompt = payload.get("prompt")
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt description must be a non-empty string."
        )

    aspect_ratio = payload.get("aspect_ratio")
    if aspect_ratio and not validate_aspect_ratio(aspect_ratio):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported aspect ratio: '{aspect_ratio}'. Allowed values: {list(ASPECT_RATIOS.keys())}"
        )

    style = payload.get("style")
    if style and not validate_style(style):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported style preset: '{style}'. Allowed values: {list(STYLE_LIBRARY.keys())}"
        )

    model = payload.get("model")
    if model and model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported model: '{model}'."
        )
