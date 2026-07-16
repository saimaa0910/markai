import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.client = httpx.Client(timeout=30.0)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            system_instructions = [m["content"] for m in messages if m["role"] == "system"]
            user_prompts = [m["content"] for m in messages if m["role"] == "user"]
            instruction_prefix = f"System Context: {system_instructions[0]}\n" if system_instructions else ""
            prompt_content = user_prompts[-1] if user_prompts else ""

            return {
                "content": f"{instruction_prefix}[Simulated OpenRouter Router ({model})]: Simulated response to prompt: '{prompt_content}'",
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "latency_ms": 70,
                "provider": "openrouter",
                "model": model,
            }
        elif not self.api_key:
            raise RuntimeError("OpenRouter API key is not configured.")

        start_time = time.perf_counter()
        response = self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://viptant.ai",
                "X-Title": "Viptant AI Platform",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                **kwargs,
            },
        )
        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "content": data["choices"][0]["message"]["content"],
            "prompt_tokens": data["usage"]["prompt_tokens"],
            "completion_tokens": data["usage"]["completion_tokens"],
            "latency_ms": latency_ms,
            "provider": "openrouter",
            "model": model,
        }

    def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            mock_text = f"[Simulated OpenRouter Stream ({model})]: Content here."
            for word in mock_text.split(" "):
                time.sleep(0.02)
                yield {
                    "content": word + " ",
                    "prompt_tokens": 5,
                    "completion_tokens": 10,
                }
            return
        elif not self.api_key:
            raise RuntimeError("OpenRouter API key is not configured.")

        with self.client.stream(
            "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://viptant.ai",
                "X-Title": "Viptant AI Platform",
            },
            json={
                "model": model,
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
        raise NotImplementedError("OpenRouter adapter does not implement embeddings.")

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
        self, messages: List[Dict[str, str]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        return self.chat(
            messages=messages,
            model=model,
            response_format={"type": "json_object"},
        )

    def health(self) -> bool:
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            return True
        if not self.api_key:
            return False
        try:
            self.chat(
                messages=[{"role": "user", "content": "ping"}],
                model="meta-llama/llama-3-8b-instruct:free",
                max_tokens=1,
            )
            return True
        except Exception:
            return False
