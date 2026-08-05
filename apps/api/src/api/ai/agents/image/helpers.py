from typing import Dict, List, Any, Optional

LIGHTING_PRESETS = {
    "studio": "soft diffuse studio lighting, professional portrait lights, clean key lights",
    "dramatic": "chiaroscuro, deep high-contrast shadows, cinematic key illumination",
    "natural": "warm golden hour sunlight, soft window shadows, realistic outdoor lighting",
    "neon": "cyberpunk neon glow, pink and cyan highlights, moody low light contrast",
    "flat": "clean vector shading, uniform ambient light, shadowless flat design",
}

CAMERA_PRESETS = {
    "close_up": "macro close-up shot, shallow depth of field, sharp detail focus",
    "portrait": "85mm lens portrait, blurry bokeh background, clear subject composition",
    "wide_angle": "wide-angle architectural capture, spacious perspective view",
    "isometric": "isometric 3D diorama angle, orthographic view",
    "eye_level": "standard eye-level shot, natural field perspective",
}

MOOD_PRESETS = {
    "energetic": "vibrant intense colors, high dynamic range, lively setting",
    "minimalist": "calm muted colors, serene simplicity, peaceful negative space",
    "mysterious": "misty foggy atmosphere, cold blue shadows, low key lighting",
    "luxurious": "refined gold tones, elegant layout, premium corporate polish",
}


def list_presets() -> Dict[str, List[str]]:
    """Lists all styling, lighting, camera and mood presets."""
    from api.ai.agents.image.constants import STYLE_LIBRARY
    return {
        "styles": list(STYLE_LIBRARY.keys()),
        "lighting": list(LIGHTING_PRESETS.keys()),
        "camera": list(CAMERA_PRESETS.keys()),
        "mood": list(MOOD_PRESETS.keys()),
    }


def compile_presets_description(
    style: Optional[str] = None,
    lighting: Optional[str] = None,
    camera: Optional[str] = None,
    mood: Optional[str] = None
) -> str:
    """Formats preset settings to a descriptive sentence."""
    parts = []
    
    # Style
    if style:
        from api.ai.agents.image.constants import STYLE_LIBRARY
        desc = STYLE_LIBRARY.get(style.lower())
        if desc:
            parts.append(f"Style: {desc}")
            
    # Lighting
    if lighting:
        desc = LIGHTING_PRESETS.get(lighting.lower())
        if desc:
            parts.append(f"Lighting: {desc}")
            
    # Camera
    if camera:
        desc = CAMERA_PRESETS.get(camera.lower())
        if desc:
            parts.append(f"Camera angle: {desc}")
            
    # Mood
    if mood:
        desc = MOOD_PRESETS.get(mood.lower())
        if desc:
            parts.append(f"Mood: {desc}")
            
    return ". ".join(parts)
