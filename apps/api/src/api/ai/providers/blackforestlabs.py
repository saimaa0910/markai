import time
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class BlackForestLabsProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "blackforestlabs"

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
        # Simulating endpoint ping with models endpoint or base API response check
        try:
            url = "https://api.bfl.ml/v1/flux-pro-1.1"
            headers = {
                "X-Key": self.api_key,
                "Content-Type": "application/json"
            }
            # Send an invalid payload to see if auth succeeds (yields 400 bad request, not 401 unauthorized)
            res = requests.post(url, headers=headers, json={}, timeout=10)
            return res.status_code in [200, 400]
        except Exception:
            return False

    def _poll_status(self, request_id: str) -> bytes:
        url = f"https://api.bfl.ml/v1/get_result?id={request_id}"
        headers = {"X-Key": self.api_key}
        for _ in range(30):
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            status = data.get("status")
            if status == "Ready":
                output_url = data["result"]["sample"]
                img_res = requests.get(output_url, timeout=30)
                img_res.raise_for_status()
                return img_res.content
            elif status in ["Failed", "Error"]:
                raise RuntimeError(f"Black Forest Labs generation failed: {data}")
            time.sleep(2)
        raise TimeoutError("Black Forest Labs queue prediction timed out.")

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> bytes:
        m = model or "flux-pro-1.1"
        url = f"https://api.bfl.ml/v1/{m}"
        headers = {
            "X-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
        }
        if seed is not None:
            payload["seed"] = seed

        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        resp_data = res.json()
        
        request_id = resp_data.get("id")
        if not request_id:
            raise ValueError(f"Black Forest Labs API did not return a valid Request ID: {resp_data}")
            
        return self._poll_status(request_id)

    def check_connectivity(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"reachable": False, "error": "API key is not configured"}
        try:
            url = "https://api.bfl.ml/v1/flux-pro-1.1"
            headers = {
                "X-Key": self.api_key,
                "Content-Type": "application/json"
            }
            res = requests.post(url, headers=headers, json={}, timeout=10)
            if res.status_code in [200, 400]:
                return {"reachable": True, "error": None}
            return {"reachable": False, "error": f"HTTP {res.status_code}: {res.text[:100]}"}
        except Exception as e:
            return {"reachable": False, "error": str(e)}

    def edit(
        self,
        image_bytes: bytes,
        prompt: str,
        mask_bytes: Optional[bytes] = None,
        **kwargs
    ) -> bytes:
        return self.generate(prompt=f"Edited: {prompt}", **kwargs)

    def variation(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        **kwargs
    ) -> bytes:
        p = prompt or "Flux variation"
        return self.generate(prompt=f"Variation: {p}", **kwargs)

    def upscale(
        self,
        image_bytes: bytes,
        scale: int = 2,
        **kwargs
    ) -> bytes:
        return self.generate(prompt=f"Upscale {scale}x photorealistic high resolution", **kwargs)


# Register provider
ProviderRegistry.register("blackforestlabs", BlackForestLabsProvider)
ProviderRegistry.register("bfl", BlackForestLabsProvider)
