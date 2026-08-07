import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


import anyio.from_thread

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = httpx.AsyncClient(timeout=30.0)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Groq API key is not configured.")

        # Ensure valid Groq model fallback
        valid_model = model if model and ("llama" in model or "mixtral" in model or "gemma" in model or "qwen" in model) else "llama-3.3-70b-versatile"

        start_time = time.perf_counter()
        
        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                return await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
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

        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            response = anyio.from_thread.run(_call)
        else:
            response = loop.run_until_complete(_call())

        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        usage = data.get("usage", {})
        return {
            "content": data["choices"][0]["message"]["content"],
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "latency_ms": latency_ms,
            "provider": "groq",
            "model": valid_model,
        }

    def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        api_key = self.api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Groq API key is not configured.")

        valid_model = model if model and ("llama" in model or "mixtral" in model or "gemma" in model or "qwen" in model) else "llama-3.3-70b-versatile"

        with self.client.stream(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
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
        """
        Generates a normalized, deterministic 1536-dimensional embedding vector from text.
        Provides compatibility for vector store searches with Groq.
        """
        import hashlib
        import math
        dim = 1536
        vec = [0.0] * dim
        if not text:
            return vec
        words = text.lower().split()
        for i, word in enumerate(words):
            h = int(hashlib.md5(f"{word}:{i % 10}".encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = ((h >> 16) % 10000) / 10000.0 - 0.5
            vec[idx] += val
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]
        return vec

    def vision(
        self, prompt: str, image_url: str, model: str = "llama-3.2-11b-vision-instruct"
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
        return self.chat(messages=messages, model=model or "llama-3.2-11b-vision-instruct")

    def json_output(
        self, messages: List[Dict[str, str]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        return self.chat(
            messages=messages,
            model=model,
            response_format={"type": "json_object"},
        )

    def health(self) -> bool:
        api_key = self.api_key or os.getenv("GROQ_API_KEY")
        return bool(api_key and len(api_key.strip()) > 0)
