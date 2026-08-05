import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class PollinationsProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "pollinations"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_generation": True,
            "supports_editing": True,
            "supports_variation": True,
            "supports_upscale": False,
            "supports_background_removal": False,
            "supports_background_replacement": False,
            "supports_inpainting": False,
            "supports_outpainting": False,
            "supports_streaming": True,
            "supports_seed": True,
            "supports_cfg_scale": False,
            "supports_negative_prompt": True,
            "supports_steps": False,
        }

    def health(self) -> bool:
        try:
            res = requests.get("https://image.pollinations.ai/prompt/healthcheck?width=16&height=16", timeout=10)
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
        m = model if model and "flux" in model.lower() else "flux"
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width={width}&height={height}&model={m}&nologo=true"
        if seed is not None:
            url += f"&seed={seed}"
        if negative_prompt:
            url += f"&negative={requests.utils.quote(negative_prompt)}"

        res = requests.get(url, timeout=45)
        res.raise_for_status()
        return res.content

    def edit(self, image_url: str, prompt: str, **kwargs) -> bytes:
        # Prompt wrap editing fallback
        edit_prompt = f"Modify image from {image_url}: {prompt}"
        return self.generate(prompt=edit_prompt, **kwargs)

    def variation(self, image_url: str, **kwargs) -> bytes:
        var_prompt = f"Visual variation of product image: {image_url}"
        return self.generate(prompt=var_prompt, **kwargs)


# Register provider
ProviderRegistry.register("pollinations", PollinationsProvider)
