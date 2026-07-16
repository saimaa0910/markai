import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = httpx.Client(timeout=10.0)  # Shorter timeout for ultra-low latency

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
                "content": f"{instruction_prefix}[Simulated Groq Router ({model})]: Simulated response to prompt: '{prompt_content}'",
                "prompt_tokens": 12,
                "completion_tokens": 18,
                "latency_ms": 10,
                "provider": "groq",
                "model": model,
            }
        elif not self.api_key:
            raise RuntimeError("Groq API key is not configured.")

        start_time = time.perf_counter()
        response = self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
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
            "provider": "groq",
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
            mock_text = f"[Simulated Groq Stream ({model})]: Fast streaming content."
            for word in mock_text.split(" "):
                time.sleep(0.01)
                yield {
                    "content": word + " ",
                    "prompt_tokens": 8,
                    "completion_tokens": 12,
                }
            return
        elif not self.api_key:
            raise RuntimeError("Groq API key is not configured.")

        with self.client.stream(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
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
        # Groq does not support native embeddings, return mock/raise error
        return [0.0] * 1536

    def vision(
        self, prompt: str, image_url: str, model: str
    ) -> Dict[str, Any]:
        # Delegate vision to OpenAI / other supported models if needed
        raise NotImplementedError("Groq does not support vision inputs.")

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
                model="llama3-8b-8192",
                max_tokens=1,
            )
            return True
        except Exception:
            return False
