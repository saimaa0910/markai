import os
import time
import json
import httpx
from typing import Generator, List, Dict, Any
from api.ai.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
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
        if not self.api_key:
            system_instructions = [m["content"] for m in messages if m["role"] == "system"]
            user_prompts = [m["content"] for m in messages if m["role"] == "user"]
            instruction_prefix = f"System Context: {system_instructions[0]}\n" if system_instructions else ""
            prompt_content = user_prompts[-1] if user_prompts else ""

            return {
                "content": f"{instruction_prefix}[Simulated Gemini Router ({model})]: Simulated response to prompt: '{prompt_content}'",
                "prompt_tokens": 16,
                "completion_tokens": 20,
                "latency_ms": 90,
                "provider": "google",
                "model": model,
            }

        payload = self._prepare_payload(messages, temperature)
        start_time = time.perf_counter()
        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
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
        if not self.api_key:
            mock_text = f"[Simulated Gemini Stream ({model})]: Streamed response."
            for word in mock_text.split(" "):
                time.sleep(0.02)
                yield {
                    "content": word + " ",
                    "prompt_tokens": 10,
                    "completion_tokens": 15,
                }
            return

        payload = self._prepare_payload(messages, temperature)
        with self.client.stream(
            "POST",
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                # Gemini returns JSON chunks (sometimes structured as SSE or array segments)
                # Parse lines to extract candidates contents
                try:
                    # In streamGenerateContent, chunks can be formatted as individual JSON lines
                    # Clean brackets/commas if streamed as JSON Array
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
        if not self.api_key:
            return [0.02] * 1536

        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={self.api_key}",
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
        # Handle vision by passing text and image data parameters (can fetch via http first)
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
        payload = self._prepare_payload(messages, 0.2)
        # Enforce json response mime type
        payload["generationConfig"]["responseMimeType"] = "application/json"
        
        if not self.api_key:
            return {
                "content": "{}",
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "latency_ms": 10,
                "provider": "google",
                "model": model,
            }

        response = self.client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
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
        if not self.api_key:
            return True
        try:
            self.chat(
                messages=[{"role": "user", "content": "ping"}],
                model="gemini-1.5-flash",
            )
            return True
        except Exception:
            return False
