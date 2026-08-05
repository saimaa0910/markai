import io
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class StabilityProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "stability"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_generation": True,
            "supports_editing": True,
            "supports_variation": False,
            "supports_upscale": True,
            "supports_background_removal": True,
            "supports_background_replacement": True,
            "supports_inpainting": True,
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
            url = "https://api.stability.ai/v1/user/account"
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
        **kwargs
    ) -> bytes:
        # Calls the Stable Image Core API
        url = "https://api.stability.ai/v2beta/stable-image/generate/core"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }
        
        # Core aspect ratio support mapping
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
            
        data = {
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": aspect_ratio,
        }
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed is not None:
            data["seed"] = seed

        res = requests.post(url, headers=headers, files={"none": ""}, data=data, timeout=60)
        res.raise_for_status()
        return res.content

    def edit(
        self,
        image_bytes: bytes,
        prompt: str,
        mask_bytes: Optional[bytes] = None,
        **kwargs
    ) -> bytes:
        url = "https://api.stability.ai/v2beta/stable-image/edit/inpaint"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }
        files = {
            "image": ("image.png", io.BytesIO(image_bytes), "image/png"),
        }
        if mask_bytes:
            files["mask"] = ("mask.png", io.BytesIO(mask_bytes), "image/png")
        data = {
            "prompt": prompt,
            "output_format": "png"
        }
        res = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        res.raise_for_status()
        return res.content

    def upscale(self, image_bytes: bytes, scale: float = 2.0, **kwargs) -> bytes:
        url = "https://api.stability.ai/v2beta/stable-image/upscale/fast"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }
        files = {
            "image": ("image.png", io.BytesIO(image_bytes), "image/png"),
        }
        res = requests.post(url, headers=headers, files=files, data={"output_format": "png"}, timeout=60)
        res.raise_for_status()
        return res.content


# Register provider
ProviderRegistry.register("stability", StabilityProvider)
