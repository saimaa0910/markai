"""
EAIMOS AI Gateway & LLM Orchestration Constants
================================================
Constants for Sprint 3: AI Gateway, Prompt Engineering, Model Routing,
RAG Engine, Memory Management, Token Metering, and AGUI Streaming Protocol.
"""

from typing import Dict, Any, Set

# ─── Model Providers & Models ───────────────────────────────────────────────

SUPPORTED_AI_PROVIDERS: Set[str] = {
    "openai", "google", "anthropic", "groq", "deepseek", "cohere", "mistral", "local"
}

DEFAULT_MODEL_PER_PROVIDER: Dict[str, str] = {
    "openai": "gpt-4o",
    "google": "gemini-1.5-pro",
    "anthropic": "claude-3-5-sonnet-20241022",
    "groq": "llama-3.3-70b-versatile",
    "deepseek": "deepseek-chat",
}

DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSION: int = 1536

# ─── Token Pricing (USD per 1k tokens) ──────────────────────────────────────

MODEL_PRICING_PER_1K: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.0100},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.0050},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "claude-3-5-sonnet-20241022": {"input": 0.0030, "output": 0.0150},
    "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}

# ─── Gateway Defaults & Limits ──────────────────────────────────────────────

GATEWAY_DEFAULT_TIMEOUT_SECONDS: float = 30.0
GATEWAY_MAX_TIMEOUT_SECONDS: float = 120.0
GATEWAY_MAX_RETRIES: int = 3
GATEWAY_BACKOFF_FACTOR: float = 1.5

# ─── RAG & Vector Store ─────────────────────────────────────────────────────

DEFAULT_CHUNK_SIZE: int = 1000
DEFAULT_CHUNK_OVERLAP: int = 200
DEFAULT_SIMILARITY_THRESHOLD: float = 0.70
DEFAULT_TOP_K_RESULTS: int = 5
MAX_TOP_K_RESULTS: int = 50

# ─── Memory & Summarization ─────────────────────────────────────────────────

DEFAULT_MEMORY_WINDOW_SIZE: int = 20  # Keep last 20 messages in short-term buffer
MEMORY_SUMMARIZATION_THRESHOLD: int = 30 # Trigger LLM background summary after 30 msgs
MAX_MEMORY_TOKEN_BUDGET: int = 4096

# ─── Prompt Engineering ─────────────────────────────────────────────────────

PROMPT_VAR_REGEX: str = r"\{\{([a-zA-Z0-9_]+)\}\}"
MAX_PROMPT_TEMPLATE_LENGTH: int = 50000
MAX_PROMPT_VARIABLES: int = 50
