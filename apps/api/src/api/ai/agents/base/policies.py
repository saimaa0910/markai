from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentPolicies(BaseModel):
    allowed_models: List[str] = Field(default_factory=lambda: ["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"])
    allowed_providers: List[str] = Field(default_factory=lambda: ["openai", "google", "groq"])
    temperature: float = 0.7
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    max_cost: float = 10.0
    max_runtime_sec: int = 300
    max_iterations: int = 10
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 3, "backoff": "exponential"})
    fallback_provider: Optional[str] = None
    reflection_threshold: float = 0.8
    evaluation_threshold: float = 0.8
    streaming: bool = True
    memory_strategy: str = "window"
    knowledge_strategy: str = "rag"
