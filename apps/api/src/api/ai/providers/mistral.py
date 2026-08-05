import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class MistralProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.base_url = (base_url or "https://api.mistral.ai/v1").rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("Mistral API key is not configured.")

        valid_model = model or "mistral-large-latest"

        start_time = time.perf_counter()
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": valid_model,
                "messages": messages,
                "temperature": temperature,
                **kwargs,
            },
        )
        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        usage = data.get("usage", {})
        return {
            "content": data["choices"][0]["message"]["content"],
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "latency_ms": latency_ms,
            "provider": "mistral",
            "model": valid_model,
        }

    def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        api_key = self.api_key or os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("Mistral API key is not configured.")

        valid_model = model or "mistral-large-latest"

        with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": valid_model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
                **kwargs,
            },
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield {
                                "content": content,
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                            }
                    except Exception:
                        pass

    def embeddings(self, text: str, model: str) -> List[float]:
        api_key = self.api_key or os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("Mistral API key is not configured.")

        response = self.client.post(
            f"{self.base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"input": text, "model": model or "mistral-embed"},
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    def vision(
        self, prompt: str, image_url: str, model: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Mistral provider does not implement vision.")

    def json_output(
        self, messages: List[Dict[str, str]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        return self.chat(
            messages=messages,
            model=model,
            response_format={"type": "json_object"},
        )

    def health(self) -> bool:
        api_key = self.api_key or os.getenv("MISTRAL_API_KEY")
        return bool(api_key and len(api_key.strip()) > 0)
