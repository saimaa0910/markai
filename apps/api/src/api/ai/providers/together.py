import base64
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class TogetherProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "together"

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
            "supports_cfg_scale": True,
            "supports_negative_prompt": True,
            "supports_steps": True,
        }

    def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            url = "https://api.together.xyz/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
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
        cfg_scale: Optional[float] = None,
        steps: Optional[int] = None,
        **kwargs
    ) -> bytes:
        url = "https://api.together.xyz/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        m = model or "stabilityai/stable-diffusion-xl-base-1.0"
        payload = {
            "model": m,
            "prompt": prompt,
            "width": width,
            "height": height,
            "n": 1,
            "response_format": "b64_json"
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed
        if cfg_scale is not None:
            payload["guidance_scale"] = cfg_scale
        if steps is not None:
            payload["steps"] = steps

        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        resp_data = res.json()
        b64_data = resp_data["data"][0]["b64_json"]
        return base64.b64decode(b64_data)


# Register provider
ProviderRegistry.register("together", TogetherProvider)
