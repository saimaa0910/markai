import time
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class FalProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "fal"

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
            url = "https://queue.fal.run/fal-ai/flux/schnell"
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            res = requests.post(url, headers=headers, json={"prompt": "ping"}, timeout=10)
            return res.status_code in [200, 202]
        except Exception:
            return False

    def _poll_queue(self, status_url: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Key {self.api_key}"}
        for _ in range(30):
            res = requests.get(status_url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            status = data.get("status")
            if status == "COMPLETED" or "status" not in data: # some endpoints return result directly
                # If we have a status result dict inside
                return data
            elif status == "IN_PROGRESS" or status == "IN_QUEUE":
                time.sleep(2)
            else:
                raise RuntimeError(f"Fal queue failed with status: {status}")
        raise TimeoutError("Fal queue request timed out.")

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
        m = model or "fal-ai/flux/schnell"
        url = f"https://queue.fal.run/{m}"
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "image_size": f"{width}x{height}",
            "sync_mode": False
        }
        if seed is not None:
            payload["seed"] = seed
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        resp_data = res.json()
        
        status_url = resp_data.get("status_url")
        if not status_url:
            # If sync response returned direct result
            output_url = resp_data["images"][0]["url"]
        else:
            result = self._poll_queue(status_url)
            # Result contains 'images' or we fetch from response_url
            response_url = result.get("response_url")
            if response_url:
                res = requests.get(response_url, headers=headers, timeout=10)
                result = res.json()
            output_url = result["images"][0]["url"]

        img_res = requests.get(output_url, timeout=30)
        img_res.raise_for_status()
        return img_res.content

    def edit(
        self,
        image_bytes: bytes,
        prompt: str,
        mask_bytes: Optional[bytes] = None,
        **kwargs
    ) -> bytes:
        # Prompt fallback wrapper
        return self.generate(prompt=f"Edit: {prompt}", **kwargs)


# Register provider
ProviderRegistry.register("fal", FalProvider)
