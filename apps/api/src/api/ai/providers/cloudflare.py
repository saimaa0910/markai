import os
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class CloudflareProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")

    @property
    def name(self) -> str:
        return "cloudflare"

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
        if not self.api_key or not self.account_id:
            return False
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            res = requests.post(url, headers=headers, json={"prompt": "ping"}, timeout=10)
            return res.status_code == 200
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
        m = model or "@cf/stabilityai/stable-diffusion-xl-base-1.0"
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{m}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
        }
        if seed is not None:
            payload["seed"] = seed

        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.content


# Register provider
ProviderRegistry.register("cloudflare", CloudflareProvider)
