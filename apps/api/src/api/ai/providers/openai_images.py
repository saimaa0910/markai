import io
import base64
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class OpenAIImagesProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "openai"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_generation": True,
            "supports_editing": True,
            "supports_variation": True,
            "supports_upscale": False,
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
            url = "https://api.openai.com/v1/models"
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
        model: Optional[str] = None,
        **kwargs
    ) -> bytes:
        url = "https://api.openai.com/v1/images/generations"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        size = f"{width}x{height}"
        if size not in ["1024x1024", "1024x1792", "1792x1024"]:
            size = "1024x1024"

        payload = {
            "model": model or "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json"
        }
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        b64_data = data["data"][0]["b64_json"]
        return base64.b64decode(b64_data)

    def edit(
        self,
        image_bytes: bytes,
        prompt: str,
        mask_bytes: Optional[bytes] = None,
        **kwargs
    ) -> bytes:
        url = "https://api.openai.com/v1/images/edits"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        files = {
            "image": ("image.png", io.BytesIO(image_bytes), "image/png"),
        }
        if mask_bytes:
            files["mask"] = ("mask.png", io.BytesIO(mask_bytes), "image/png")
            
        data = {
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }
        
        res = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        res.raise_for_status()
        res_data = res.json()
        b64_data = res_data["data"][0]["b64_json"]
        return base64.b64decode(b64_data)

    def variation(self, image_bytes: bytes, **kwargs) -> bytes:
        url = "https://api.openai.com/v1/images/variations"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {
            "image": ("image.png", io.BytesIO(image_bytes), "image/png"),
        }
        data = {
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }
        res = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        res.raise_for_status()
        res_data = res.json()
        b64_data = res_data["data"][0]["b64_json"]
        return base64.b64decode(b64_data)


# Register provider
ProviderRegistry.register("openai", OpenAIImagesProvider)
