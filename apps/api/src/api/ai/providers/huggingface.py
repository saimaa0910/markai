import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class HuggingFaceProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "huggingface"

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
            "supports_negative_prompt": False,
            "supports_steps": False,
        }

    def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Ping stable diffusion on HF
            url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            res = requests.post(url, headers=headers, json={"inputs": "healthcheck"}, timeout=10)
            return res.status_code in [200, 503]  # 503 means loading, which is still connected
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> bytes:
        model_id = model or "black-forest-labs/FLUX.1-schnell"
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "width": width,
                "height": height,
            }
        }
        if seed is not None:
            payload["parameters"]["seed"] = seed

        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.content


# Register provider
ProviderRegistry.register("huggingface", HuggingFaceProvider)
