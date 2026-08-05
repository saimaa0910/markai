import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class IdeogramProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "ideogram"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_generation": True,
            "supports_editing": False,
            "supports_variation": False,
            "supports_upscale": False,
            "supports_background_removal": False,
            "supports_background_replacement": False,
            "supports_inpainting": False,
            "supports_outpainting": False,
            "supports_streaming": False,
            "supports_seed": True,
            "supports_cfg_scale": False,
            "supports_negative_prompt": True,
            "supports_steps": False,
        }

    def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            url = "https://api.ideogram.ai/manage/user"
            headers = {"Api-Key": self.api_key}
            res = requests.get(url, headers=headers, timeout=10)
            return res.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> bytes:
        url = "https://api.ideogram.ai/generate"
        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        aspect_ratio = "ASPECT_1_1"
        ratio = float(width) / float(height)
        if ratio > 1.5:
            aspect_ratio = "ASPECT_16_9"
        elif ratio < 0.6:
            aspect_ratio = "ASPECT_9_16"
        elif ratio > 1.2:
            aspect_ratio = "ASPECT_3_2"
        elif ratio < 0.8:
            aspect_ratio = "ASPECT_2_3"

        payload = {
            "image_request": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "model": model or "V_2"
            }
        }
        if seed is not None:
            payload["image_request"]["seed"] = seed
        if negative_prompt:
            payload["image_request"]["negative_prompt"] = negative_prompt

        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        resp_data = res.json()
        
        output_url = resp_data["data"][0]["url"]
        img_res = requests.get(output_url, timeout=30)
        img_res.raise_for_status()
        return img_res.content


# Register provider
ProviderRegistry.register("ideogram", IdeogramProvider)
