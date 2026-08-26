import abc
import time
import asyncio
from typing import AsyncGenerator, Generator, List, Dict, Any, Optional
import httpx


class BaseLLMProvider(abc.ABC):
    """
    Abstract base class for all LLM Provider Adapters.
    Designed for async-first operation with full httpx.AsyncClient integration
    and synchronous compatibility fallbacks.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self._async_client: Optional[httpx.AsyncClient] = None

    def _get_async_client(self, timeout: float = 30.0) -> httpx.AsyncClient:
        """Get or initialize persistent AsyncClient."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=timeout)
        return self._async_client

    async def aclose(self) -> None:
        """Close underlying async HTTP client session."""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    @abc.abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute chat completion.
        Returns a dict containing:
        - 'content': Response string
        - 'prompt_tokens': Number of input tokens
        - 'completion_tokens': Number of output tokens
        - 'latency_ms': Execution latency
        - 'provider': Provider identifier name
        - 'model': Model name used
        """
        pass

    @abc.abstractmethod
    def stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute streaming chat completion yielding chunk dictionaries.
        """
        pass

    @abc.abstractmethod
    def embeddings(self, text: str, model: str) -> List[float]:
        """
        Generate vector embedding for input text.
        """
        pass

    @abc.abstractmethod
    def vision(
        self, prompt: str, image_url: str, model: str
    ) -> Dict[str, Any]:
        """
        Analyze an image URL with multimodal input.
        """
        pass

    @abc.abstractmethod
    def json_output(
        self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        """
        Retrieve structured JSON output matching target schema.
        """
        pass

    @abc.abstractmethod
    def health(self) -> bool:
        """
        Check if the provider configuration is present.
        """
        pass

    def check_connectivity(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Perform a real network liveness check against the provider API.
        Subclasses override this to hit model list / ping endpoints.

        Returns:
            dict with keys: reachable (bool), latency_ms (int), error (str|None)
        """
        start = time.perf_counter()
        try:
            ok = self.health()
            latency = int((time.perf_counter() - start) * 1000)
            return {"reachable": ok, "latency_ms": latency, "error": None}
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"reachable": False, "latency_ms": latency, "error": str(e)}
