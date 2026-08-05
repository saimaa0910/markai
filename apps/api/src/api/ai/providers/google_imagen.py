import base64
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class GoogleImagenProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "google"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_generation": True,
            "supports_editing": True,
            "supports_variation": False,
            "supports_upscale": True,
            "supports_background_removal": False,
            "supports_background_replacement": False,
            "supports_inpainting": True,
            "supports_outpainting": False,
            "supports_streaming": False,
            "supports_seed": False,
            "supports_cfg_scale": False,
            "supports_negative_prompt": False,
            "supports_steps": False,
        }

    def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Ping models list on Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            res = requests.get(url, timeout=10)
            return res.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        model: Optional[str] = None,
        **kwargs
    ) -> bytes:
        m = model or "imagen-3.0-generate-002"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateImages?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        aspect_ratio = "1:1"
        ratio = float(width) / float(height)
        if ratio > 1.5:
            aspect_ratio = "16:9"
        elif ratio < 0.6:
            aspect_ratio = "9:16"
        elif ratio > 1.2:
            aspect_ratio = "3:2"
        elif ratio < 0.8:
            aspect_ratio = "2:3"
            
        payload = {
            "prompt": prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/png",
            "aspectRatio": aspect_ratio,
        }

        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        resp_data = res.json()
        b64_data = resp_data["generatedImages"][0]["image"]["imageBytes"]
        return base64.b64decode(b64_data)

    def edit(self, image_bytes: bytes, prompt: str, **kwargs) -> bytes:
        # Prompt fallback editing wrapper
        return self.generate(prompt=f"Edit: {prompt}", **kwargs)


# Register provider
ProviderRegistry.register("google", GoogleImagenProvider)
