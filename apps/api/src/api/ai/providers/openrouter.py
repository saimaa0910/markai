import os
import time
import json
import httpx
import asyncio
from typing import AsyncGenerator, Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key=api_key or os.getenv("OPENROUTER_API_KEY"))
        self.base_url = "https://openrouter.ai/api/v1"

    async def achat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OpenRouter API key is not configured.")

        valid_model = model or "openai/gpt-4o-mini"
        start_time = time.perf_counter()

        client = self._get_async_client()
        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://viptant.ai",
                "X-Title": "Viptant AI Platform",
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
            "provider": "openrouter",
            "model": valid_model,
        }

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OpenRouter API key is not configured.")

        valid_model = model or "openai/gpt-4o-mini"
        start_time = time.perf_counter()

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://viptant.ai",
                    "X-Title": "Viptant AI Platform",
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
                "provider": "openrouter",
                "model": valid_model,
            }

    async def astream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OpenRouter API key is not configured.")

        valid_model = model or "openai/gpt-4o-mini"
        client = self._get_async_client()

        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://viptant.ai",
                "X-Title": "Viptant AI Platform",
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
            async for line in response.aiter_lines():
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

    def stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OpenRouter API key is not configured.")

        valid_model = model or "openai/gpt-4o-mini"

        with httpx.Client(timeout=30.0) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://viptant.ai",
                    "X-Title": "Viptant AI Platform",
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
        raise NotImplementedError("OpenRouter chat completions adapter does not implement embeddings.")

    async def aembeddings(self, text: str, model: str) -> List[float]:
        raise NotImplementedError("OpenRouter chat completions adapter does not implement embeddings.")

    def vision(
        self, prompt: str, image_url: str, model: str
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]
        return self.chat(messages=messages, model=model)

    def json_output(
        self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        return self.chat(
            messages=messages,
            model=model,
            response_format={"type": "json_object"},
        )

    def health(self) -> bool:
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        return bool(api_key and len(api_key.strip()) > 0)

    async def acheck_connectivity(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Real async network liveness check against OpenRouter models API.
        """
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {"reachable": False, "latency_ms": 0, "error": "OpenRouter API key is not configured."}
        start = time.perf_counter()
        try:
            client = self._get_async_client(timeout=timeout)
            res = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            latency = int((time.perf_counter() - start) * 1000)
            if res.status_code == 200:
                return {"reachable": True, "latency_ms": latency, "error": None}
            return {
                "reachable": False,
                "latency_ms": latency,
                "error": f"HTTP {res.status_code}",
            }
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"reachable": False, "latency_ms": latency, "error": str(e)}

    def check_connectivity(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Real network liveness check against OpenRouter models API.
        """
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {"reachable": False, "latency_ms": 0, "error": "OpenRouter API key is not configured."}
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            latency = int((time.perf_counter() - start) * 1000)
            if res.status_code == 200:
                return {"reachable": True, "latency_ms": latency, "error": None}
            return {
                "reachable": False,
                "latency_ms": latency,
                "error": f"HTTP {res.status_code}",
            }
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"reachable": False, "latency_ms": latency, "error": str(e)}
