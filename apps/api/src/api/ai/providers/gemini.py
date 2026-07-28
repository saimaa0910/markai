import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = httpx.Client(timeout=30.0)

    def _prepare_payload(self, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        """
        Converts standard messages lists to Gemini contents:
        - Maps 'assistant' role to 'model'.
        - Extracts 'system' messages into 'systemInstruction'.
        """
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

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            combined = " ".join(m.get("content", "") for m in messages)
            return {
                "content": f"Gemini Router ({model}) simulated response. Context: {combined}",
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "latency_ms": 10,
                "provider": "google",
                "model": model,
            }
        elif not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        payload = self._prepare_payload(messages, temperature)
        start_time = time.perf_counter()
        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
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
            "model": model,
        }

    def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        payload = self._prepare_payload(messages, temperature)
        with self.client.stream(
            "POST",
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}",
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

    def embeddings(self, text: str, model: str) -> List[float]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            return [0.02] * 1536
        elif not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]}
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]["values"]

    def vision(
        self, prompt: str, image_url: str, model: str
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "user",
                "content": f"{prompt}\nImage source reference: {image_url}"
            }
        ]
        return self.chat(messages=messages, model=model)

    def json_output(
        self, messages: List[Dict[str, str]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        payload = self._prepare_payload(messages, 0.2)
        payload["generationConfig"]["responseMimeType"] = "application/json"
        
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            return {
                "content": "{}",
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "latency_ms": 10,
                "provider": "google",
                "model": model,
            }
        elif not api_key:
            raise RuntimeError("Gemini API key is not configured.")

        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
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
            "model": model,
        }

    def health(self) -> bool:
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            return True
        if not self.api_key:
            return False
        try:
            self.chat(
                messages=[{"role": "user", "content": "ping"}],
                model="gemini-1.5-flash",
            )
            return True
        except Exception:
            return False
