import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any
from api.ai.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Instantiate a client that is safe to reuse
        self.client = httpx.Client(timeout=30.0)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        if not self.api_key:
            system_instructions = [m["content"] for m in messages if m["role"] == "system"]
            user_prompts = [m["content"] for m in messages if m["role"] == "user"]
            instruction_prefix = f"System Context: {system_instructions[0]}\n" if system_instructions else ""
            prompt_content = user_prompts[-1] if user_prompts else ""

            return {
                "content": f"{instruction_prefix}[Simulated OpenAI Router ({model})]: Simulated response to prompt: '{prompt_content}'",
                "prompt_tokens": 15,
                "completion_tokens": 25,
                "latency_ms": 50,
                "provider": "openai",
                "model": model,
            }

        start_time = time.perf_counter()
        response = self.client.post(
            "https://api.openai.com/v1/chat/completions",
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
            "provider": "openai",
            "model": model,
        }

    def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        if not self.api_key:
            mock_text = f"[Simulated OpenAI Stream ({model})]: Streamed response."
            for word in mock_text.split(" "):
                time.sleep(0.02)
                yield {
                    "content": word + " ",
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                }
            return

        with self.client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
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
        if not self.api_key:
            # Return standard mock embedding vector (1536 dimension)
            return [0.01] * 1536

        response = self.client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"input": text, "model": model},
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

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
        if not self.api_key:
            return True
        try:
            # Perform tiny check query
            self.chat(
                messages=[{"role": "user", "content": "ping"}],
                model="gpt-3.5-turbo",
                max_tokens=1,
            )
            return True
        except Exception:
            return False
