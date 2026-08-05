from typing import Dict, Any, List

# Providers default strategy ranking
DEFAULT_PROVIDER_PRIORITY = [
    "pollinations",
    "huggingface",
    "cloudflare",
    "deepinfra",
    "openrouter",
    "together",
    "fal",
    "replicate",
    "stability",
    "openai",
    "google",
    "ideogram",
]

# Supported aspect ratios and their dimensions shims
ASPECT_RATIOS: Dict[str, Dict[str, int]] = {
    "1:1": {"width": 1024, "height": 1024},
    "16:9": {"width": 1024, "height": 576},
    "9:16": {"width": 576, "height": 1024},
    "4:5": {"width": 800, "height": 1000},
    "3:2": {"width": 1024, "height": 683},
    "2:3": {"width": 683, "height": 1024},
    "story": {"width": 1080, "height": 1920},
    "banner": {"width": 1200, "height": 628},
}

# Style library presets description
STYLE_LIBRARY: Dict[str, str] = {
    "apple": "Clean, premium product photography, dynamic glass reflections, neutral background, soft corporate studio lighting, ultra-realistic textures, sleek design.",
    "minimal": "Minimalist composition, negative space, elegant contrast, simple shapes, subtle neutral palette, high-end design aesthetics.",
    "luxury": "Luxury branding, gold accents, deep dark backgrounds, marble textures, cinematic velvet lighting, high-contrast rich textures.",
    "corporate": "Professional corporate headshot/studio setting, friendly bright environment, business clean attire, standard corporate colors, soft diffuse light.",
    "startup": "Modern tech startup workspace, bright natural window light, lively colors, whiteboard with wireframe mockups, casual atmosphere.",
    "modern saas": "Clean tech vector illustration, sleek UI cards floating, modern purple and violet gradients, glassmorphic elements, futuristic web app design.",
    "glassmorphism": "Glassmorphism effect, translucent layers, frosted glass, vibrant glowing background, blur refraction, pastel neon highlights.",
    "clay": "Claymation style, soft matte clay renders, cute 3D character design, rounded friendly shapes, bright studio play lighting.",
    "3d": "High-fidelity 3D render, Octane Render style, glossy textures, rich depth of field, vibrant colors, volumetric light rays.",
    "illustration": "Hand-drawn digital editorial illustration, warm organic textures, flat colors, conceptual artwork.",
    "photorealistic": "Photorealistic photo, captured on 35mm lens, f/1.8 aperture, natural sunlight, intricate details, highly detailed textures.",
    "cyberpunk": "Cyberpunk cityscape, neon signs (pink, blue, yellow), wet streets with rain reflections, futuristic tech, foggy cinematic atmosphere.",
    "anime": "Modern anime style key visual, vibrant cel-shaded color scheme, dynamic composition, detailed hand-drawn linework.",
    "cartoon": "Vibrant modern cartoon style, bold lines, expressive character designs, colorful playful shapes.",
    "material": "Material Design aesthetic, flat paper cutout layers, clean drop shadows, bold primary colors, Google styling.",
    "editorial": "High fashion editorial magazine cover, dramatic avant-garde lighting, grain texture, bold composition.",
    "magazine": "Commercial print magazine ad, crisp focus, clear visual layout, professional product placement, studio clean backdrop.",
    "isometric": "Isometric 3D perspective, miniature diorama design, clean low-poly models, bright pastel lighting.",
}

# Supported image models
SUPPORTED_MODELS = [
    "flux-schnell",
    "flux-dev",
    "flux-pro",
    "sdxl",
    "sdxl-turbo",
    "sd-1.5",
    "sd-xl",
    "playground-v2",
    "playground-v2.5",
    "pixart-sigma",
    "kandinsky-3",
    "auraflow",
    "lumina",
    "sana",
    "omnigen",
    "janus-pro",
    "imagen",
    "dalle-3",
    "ideogram",
]
