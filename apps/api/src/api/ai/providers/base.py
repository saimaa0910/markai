import abc
from typing import Generator, List, Dict, Any, Optional


class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute synchronous chat completion.
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
        Each yielded dict must contain:
        - 'content': Delta content string
        - 'prompt_tokens': Input tokens count (optional/final)
        - 'completion_tokens': Output tokens count (optional/final)
        """
        pass

    @abc.abstractmethod
    def embeddings(self, text: str, model: str) -> List[float]:
        """
        Generate a 1536-dimension float vector embedding for the input text.
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
        Retrieve structured JSON output matching target Pydantic/JSON schema.
        """
        pass

    @abc.abstractmethod
    def health(self) -> bool:
        """
        Perform standard health verification check on key status/latency.
        """
        pass
