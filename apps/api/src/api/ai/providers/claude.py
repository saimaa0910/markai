import os
import time
import json
import httpx
import asyncio
from typing import AsyncGenerator, Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.base_url = "https://api.anthropic.com/v1"

    def _prepare_payload(self, messages: List[Dict[str, Any]], model: str, temperature: float, **kwargs) -> Dict[str, Any]:
        anthropic_messages = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        valid_model = model or "claude-3-5-sonnet-20240620"
        payload = {
            "model": valid_model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.pop("max_tokens", 4096),
            "temperature": temperature,
            **kwargs
        }
        if system_instruction:
            payload["system"] = system_instruction
            
        return payload

    async def achat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Claude API key is not configured.")

        valid_model = model or "claude-3-5-sonnet-20240620"
        payload = self._prepare_payload(messages, valid_model, temperature, **kwargs)
        start_time = time.perf_counter()

        client = self._get_async_client()
        response = await client.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "content": data["content"][0]["text"],
            "prompt_tokens": data["usage"]["input_tokens"],
            "completion_tokens": data["usage"]["output_tokens"],
            "latency_ms": latency_ms,
            "provider": "anthropic",
            "model": valid_model,
        }

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Claude API key is not configured.")

        valid_model = model or "claude-3-5-sonnet-20240620"
        payload = self._prepare_payload(messages, valid_model, temperature, **kwargs)
        start_time = time.perf_counter()

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            return {
                "content": data["content"][0]["text"],
                "prompt_tokens": data["usage"]["input_tokens"],
                "completion_tokens": data["usage"]["output_tokens"],
                "latency_ms": latency_ms,
                "provider": "anthropic",
                "model": valid_model,
            }

    async def astream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Claude API key is not configured.")

        valid_model = model or "claude-3-5-sonnet-20240620"
        payload = self._prepare_payload(messages, valid_model, temperature, stream=True, **kwargs)
        client = self._get_async_client()

        async with client.stream(
            "POST",
            f"{self.base_url}/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        chunk = json.loads(data_str)
                        chunk_type = chunk.get("type")
                        if chunk_type == "content_block_delta":
                            content = chunk.get("delta", {}).get("text", "")
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
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Claude API key is not configured.")

        valid_model = model or "claude-3-5-sonnet-20240620"
        payload = self._prepare_payload(messages, valid_model, temperature, stream=True, **kwargs)

        with httpx.Client(timeout=30.0) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            chunk = json.loads(data_str)
                            chunk_type = chunk.get("type")
                            if chunk_type == "content_block_delta":
                                content = chunk.get("delta", {}).get("text", "")
                                if content:
                                    yield {
                                        "content": content,
                                        "prompt_tokens": 0,
                                        "completion_tokens": 0,
                                    }
                        except Exception:
                            pass

    def embeddings(self, text: str, model: str) -> List[float]:
        raise NotImplementedError("Anthropic does not offer an embedding API. Use an embedding provider (e.g. OpenAI or Mistral).")

    async def aembeddings(self, text: str, model: str) -> List[float]:
        raise NotImplementedError("Anthropic does not offer an embedding API. Use an embedding provider (e.g. OpenAI or Mistral).")

    def vision(
        self, prompt: str, image_url: str, model: str = "claude-3-5-sonnet-20240620"
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        return self.chat(messages=messages, model=model or "claude-3-5-sonnet-20240620")

    def json_output(
        self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        json_messages = list(messages)
        json_messages.insert(0, {
            "role": "system",
            "content": f"You must output JSON matching this schema: {json.dumps(schema)}"
        })
        return self.chat(messages=json_messages, model=model)

    def health(self) -> bool:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        return bool(api_key and len(api_key.strip()) > 0)

    async def acheck_connectivity(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Real async network liveness check against Anthropic models API.
        """
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"reachable": False, "latency_ms": 0, "error": "Claude API key is not configured."}
        start = time.perf_counter()
        try:
            client = self._get_async_client(timeout=timeout)
            res = await client.get(
                f"{self.base_url}/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
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
        Real network liveness check against Anthropic models API.
        """
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"reachable": False, "latency_ms": 0, "error": "Claude API key is not configured."}
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.get(
                    f"{self.base_url}/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
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
