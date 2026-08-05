import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any, Optional
from api.ai.providers.base import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = httpx.Client(timeout=30.0)

    def _prepare_payload(self, messages: List[Dict[str, str]], model: str, temperature: float, **kwargs) -> Dict[str, Any]:
        """
        Adapts standard messages lists to Anthropic's Messages format:
        Extracts 'system' messages into the top-level 'system' field.
        """
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

        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.pop("max_tokens", 4096),
            "temperature": temperature,
            **kwargs
        }
        if system_instruction:
            payload["system"] = system_instruction
            
        return payload

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Claude API key is not configured.")

        payload = self._prepare_payload(messages, model, temperature, **kwargs)
        start_time = time.perf_counter()
        response = self.client.post(
            "https://api.anthropic.com/v1/messages",
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
            "model": model,
        }

    def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Claude API key is not configured.")

        payload = self._prepare_payload(messages, model, temperature, stream=True, **kwargs)
        with self.client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
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
        raise NotImplementedError("Anthropic does not support embeddings.")

    def vision(
        self, prompt: str, image_url: str, model: str
    ) -> Dict[str, Any]:
        # Implement vision message structure for Anthropic Messages API
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
        return self.chat(messages=messages, model=model)

    def json_output(
        self, messages: List[Dict[str, str]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        # Add system prompt instructions enforcing JSON output schema
        json_messages = messages.copy()
        json_messages.insert(0, {
            "role": "system",
            "content": f"You must output JSON matching this schema: {json.dumps(schema)}"
        })
        return self.chat(messages=json_messages, model=model)

    def health(self) -> bool:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        return bool(api_key and len(api_key.strip()) > 0)
