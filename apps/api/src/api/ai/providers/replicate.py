import time
import requests
from typing import Dict, Any, Optional
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry


class ReplicateProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "replicate"

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
            "supports_seed": True,
            "supports_cfg_scale": True,
            "supports_negative_prompt": True,
            "supports_steps": True,
        }

    def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            url = "https://api.replicate.com/v1/models/stability-ai/sdxl"
            headers = {"Authorization": f"Token {self.api_key}"}
            res = requests.get(url, headers=headers, timeout=10)
            return res.status_code == 200
        except Exception:
            return False

    def _poll_prediction(self, url: str) -> bytes:
        headers = {"Authorization": f"Token {self.api_key}"}
        # Poll prediction for up to 60 seconds
        for _ in range(30):
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            status = data.get("status")
            if status == "succeeded":
                output = data.get("output")
                output_url = output[0] if isinstance(output, list) else output
                img_res = requests.get(output_url, timeout=30)
                img_res.raise_for_status()
                return img_res.content
            elif status in ["failed", "canceled"]:
                raise RuntimeError(f"Replicate prediction failed or was canceled: {data.get('error')}")
            time.sleep(2)
        raise TimeoutError("Replicate prediction timed out.")

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
        url = "https://api.replicate.com/v1/predictions"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        # Model tag or default SDXL
        model_version = "7762fd07cf21c0fd85ab22d2d4919cc73beee26caf2c7a02ec24d115ad47a324"  # SDXL default version
        if model and ":" in model:
            model_version = model.split(":")[-1]

        payload = {
            "version": model_version,
            "input": {
                "prompt": prompt,
                "width": width,
                "height": height,
            }
        }
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["input"]["seed"] = seed

        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        pred_data = res.json()
        return self._poll_prediction(pred_data["urls"]["get"])

    def edit(
        self,
        image_bytes: bytes,
        prompt: str,
        mask_bytes: Optional[bytes] = None,
        **kwargs
    ) -> bytes:
        # Dummy or placeholder implementation calling generate
        # In production: uploads files to public hosting, and runs inpaint model
        return self.generate(prompt=f"Edit: {prompt}", **kwargs)


# Register provider
ProviderRegistry.register("replicate", ReplicateProvider)
