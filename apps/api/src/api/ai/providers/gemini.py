import os
import time
import json
import httpx
import asyncio
from typing import AsyncGenerator, Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def _prepare_payload(self, messages: List[Dict[str, Any]], temperature: float) -> Dict[str, Any]:
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            if role == "system":
                system_instruction = {"parts": [{"text": msg["content"]}]}
            else:
                gemini_role = "model" if role in ("assistant", "model") else "user"
                gemini_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": msg["content"]}]
                })

        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        return payload

    async def achat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        valid_model = model or "gemini-1.5-flash"
        payload = self._prepare_payload(messages, temperature)
        start_time = time.perf_counter()

        client = self._get_async_client()
        response = await client.post(
            f"{self.base_url}/models/{valid_model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        candidate = data["candidates"][0]
        content_text = candidate["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})

        return {
            "content": content_text,
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "latency_ms": latency_ms,
            "provider": "google",
            "model": valid_model,
        }

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        valid_model = model or "gemini-1.5-flash"
        payload = self._prepare_payload(messages, temperature)
        start_time = time.perf_counter()

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/models/{valid_model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            candidate = data["candidates"][0]
            content_text = candidate["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})

            return {
                "content": content_text,
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "latency_ms": latency_ms,
                "provider": "google",
                "model": valid_model,
            }

    async def astream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        valid_model = model or "gemini-1.5-flash"
        payload = self._prepare_payload(messages, temperature)
        client = self._get_async_client()

        async with client.stream(
            "POST",
            f"{self.base_url}/models/{valid_model}:streamGenerateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    clean_line = line.strip().lstrip("[").rstrip(",").rstrip("]")
                    if not clean_line:
                        continue
                    chunk = json.loads(clean_line)
                    candidate = chunk["candidates"][0]
                    content = candidate["content"]["parts"][0]["text"]
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
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        valid_model = model or "gemini-1.5-flash"
        payload = self._prepare_payload(messages, temperature)

        with httpx.Client(timeout=30.0) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/models/{valid_model}:streamGenerateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        clean_line = line.strip().lstrip("[").rstrip(",").rstrip("]")
                        if not clean_line:
                            continue
                        chunk = json.loads(clean_line)
                        candidate = chunk["candidates"][0]
                        content = candidate["content"]["parts"][0]["text"]
                        if content:
                            yield {
                                "content": content,
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                            }
                    except Exception:
                        pass

    async def aembeddings(self, text: str, model: str = "text-embedding-004") -> List[float]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        valid_model = model or "text-embedding-004"
        client = self._get_async_client()
        response = await client.post(
            f"{self.base_url}/models/{valid_model}:embedContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "model": f"models/{valid_model}",
                "content": {"parts": [{"text": text}]}
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]["values"]

    def embeddings(self, text: str, model: str = "text-embedding-004") -> List[float]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        valid_model = model or "text-embedding-004"
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/models/{valid_model}:embedContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "model": f"models/{valid_model}",
                    "content": {"parts": [{"text": text}]}
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]["values"]

    def vision(
        self, prompt: str, image_url: str, model: str = "gemini-1.5-flash"
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "user",
                "content": f"{prompt}\nImage source reference: {image_url}"
            }
        ]
        return self.chat(messages=messages, model=model or "gemini-1.5-flash")

    def json_output(
        self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: str = "gemini-1.5-flash"
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        valid_model = model or "gemini-1.5-flash"
        payload = self._prepare_payload(messages, 0.2)
        payload["generationConfig"]["responseMimeType"] = "application/json"

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/models/{valid_model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            candidate = data["candidates"][0]
            content_text = candidate["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})

            return {
                "content": content_text,
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "latency_ms": 100,
                "provider": "google",
                "model": valid_model,
            }

    def health(self) -> bool:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        return bool(api_key and len(api_key.strip()) > 0)

    async def acheck_connectivity(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Real async network liveness check against Gemini models API.
        """
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"reachable": False, "latency_ms": 0, "error": "Gemini API key is not configured."}
        start = time.perf_counter()
        try:
            client = self._get_async_client(timeout=timeout)
            res = await client.get(f"{self.base_url}/models?key={api_key}")
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
        Real network liveness check against Gemini models API.
        """
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"reachable": False, "latency_ms": 0, "error": "Gemini API key is not configured."}
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.get(f"{self.base_url}/models?key={api_key}")
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
