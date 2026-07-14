import uuid
import time
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from api.ai.router.engine import ModelRouter
from api.ai.registry.manager import ModelRegistryManager
from api.ai.providers.openai import OpenAIProvider
from api.ai.providers.groq import GroqProvider
from api.ai.providers.openrouter import OpenRouterProvider
from api.ai.providers.claude import ClaudeProvider
from api.ai.providers.gemini import GeminiProvider
from api.models.ai_usage import AITokenUsage
from api.models.ai_registry import AIModelRegistry


class AIGateway:
    def __init__(self) -> None:
        self.providers = {
            "openai": OpenAIProvider(),
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "anthropic": ClaudeProvider(),
            "google": GeminiProvider(),
        }
        self.router = ModelRouter()

    def _calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        input_price: Decimal,
        output_price: Decimal,
    ) -> Decimal:
        """
        Calculate total execution cost. Prices are per 1M tokens in the registry.
        """
        input_cost = (Decimal(prompt_tokens) * Decimal(input_price)) / Decimal("1000000")
        output_cost = (Decimal(completion_tokens) * Decimal(output_price)) / Decimal("1000000")
        return input_cost + output_cost

    def _log_usage(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        model_name: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: Decimal,
        latency_ms: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Write execution metrics log audit to database usage table.
        """
        usage = AITokenUsage(
            organization_id=organization_id,
            user_id=user_id,
            provider=provider,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
        )
        db.add(usage)
        db.commit()

    def chat(
        self,
        db: Session,
        messages: List[Dict[str, str]],
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        temperature: float = 0.7,
        rag_enabled: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Orchestrate chat execution with automated routing and fallback handler.
        """
        if rag_enabled and messages:
            user_msgs = [m for m in messages if m["role"] == "user"]
            if user_msgs:
                query_text = user_msgs[-1]["content"]
                from api.services.knowledge import KnowledgeService
                chunks = KnowledgeService.query_similar_chunks(
                    db=db,
                    query_text=query_text,
                    organization_id=organization_id,
                    user_id=user_id,
                    limit=3,
                )
                if chunks:
                    context_str = "\n---\n".join(c.content for c in chunks)
                    rag_instruction = (
                        f"Use the following knowledge base context to help answer the user request:\n\n{context_str}"
                    )
                    system_msgs = [m for m in messages if m["role"] == "system"]
                    if system_msgs:
                        system_msgs[0]["content"] = (
                            f"{system_msgs[0]['content']}\n\n{rag_instruction}"
                        )
                    else:
                        messages.insert(0, {"role": "system", "content": rag_instruction})

        # Ensure default models are seeded in the database
        ModelRegistryManager.seed_default_models(db)

        # Extract optional model_name requested by user
        requested_model_name = kwargs.pop("model_name", None)
        
        candidates = []
        if requested_model_name:
            from sqlalchemy import select
            db_model = db.scalars(
                select(AIModelRegistry).where(
                    AIModelRegistry.model_name == requested_model_name
                )
            ).first()
            if db_model and db_model.is_healthy:
                candidates = [db_model]

        if not candidates:
            candidates = self.router.route(db, "chat", organization_id)

        if not candidates:
            raise RuntimeError("No healthy models available in registry.")

        last_error = None
        for model_meta in candidates:
            provider_name = model_meta.provider
            adapter = self.providers.get(provider_name)
            if not adapter:
                continue

            start_time = time.perf_counter()
            try:
                # Call adapter chat completions
                res = adapter.chat(
                    messages=messages,
                    model=model_meta.model_name,
                    temperature=temperature,
                    **kwargs,
                )
                latency_ms = res.get("latency_ms", int((time.perf_counter() - start_time) * 1000))
                
                # Calculate cost mapping
                prompt_tokens = res.get("prompt_tokens", 0)
                completion_tokens = res.get("completion_tokens", 0)
                cost = self._calculate_cost(
                    prompt_tokens,
                    completion_tokens,
                    model_meta.input_token_price,
                    model_meta.output_token_price,
                )

                # Log usage audits
                self._log_usage(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    model_name=model_meta.model_name,
                    provider=provider_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    status="success",
                )
                res["cost_usd"] = cost
                res["model"] = model_meta.model_name
                return res

            except Exception as e:
                # Record adapter errors, update registry model health, log failure, and loop fallback
                last_error = e
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                ModelRegistryManager.update_model_health(db, model_meta.model_name, False)
                self._log_usage(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    model_name=model_meta.model_name,
                    provider=provider_name,
                    prompt_tokens=0,
                    completion_tokens=0,
                    cost_usd=Decimal("0.0"),
                    latency_ms=latency_ms,
                    status="failure",
                    error_message=str(e),
                )

        raise RuntimeError(f"AI Gateway failed to execute chat requests: {str(last_error)}")

    def embeddings(
        self,
        db: Session,
        text: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[float]:
        candidates = self.router.route(db, "embeddings", organization_id)
        if not candidates:
            raise RuntimeError("No healthy embeddings models registry available.")

        last_error = None
        for model_meta in candidates:
            provider_name = model_meta.provider
            adapter = self.providers.get(provider_name)
            if not adapter:
                continue

            start_time = time.perf_counter()
            try:
                vector = adapter.embeddings(text=text, model=model_meta.model_name)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                cost = self._calculate_cost(
                    len(text.split()), 0, model_meta.input_token_price, model_meta.output_token_price
                )
                self._log_usage(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    model_name=model_meta.model_name,
                    provider=provider_name,
                    prompt_tokens=len(text.split()),
                    completion_tokens=0,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    status="success",
                )
                return vector
            except Exception as e:
                last_error = e
                ModelRegistryManager.update_model_health(db, model_meta.model_name, False)

        raise RuntimeError(f"AI Gateway embeddings execution failed: {str(last_error)}")

    def vision(
        self,
        db: Session,
        prompt: str,
        image_url: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        candidates = self.router.route(db, "vision", organization_id)
        if not candidates:
            raise RuntimeError("No healthy vision models available.")

        last_error = None
        for model_meta in candidates:
            provider_name = model_meta.provider
            adapter = self.providers.get(provider_name)
            if not adapter:
                continue

            start_time = time.perf_counter()
            try:
                res = adapter.vision(prompt=prompt, image_url=image_url, model=model_meta.model_name)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                cost = self._calculate_cost(
                    100, 100, model_meta.input_token_price, model_meta.output_token_price
                )
                self._log_usage(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    model_name=model_meta.model_name,
                    provider=provider_name,
                    prompt_tokens=100,
                    completion_tokens=100,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    status="success",
                )
                return res
            except Exception as e:
                last_error = e
                ModelRegistryManager.update_model_health(db, model_meta.model_name, False)

        raise RuntimeError(f"AI Gateway vision execution failed: {str(last_error)}")

    def json_output(
        self,
        db: Session,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        candidates = self.router.route(db, "json", organization_id)
        if not candidates:
            raise RuntimeError("No healthy JSON models available.")

        last_error = None
        for model_meta in candidates:
            provider_name = model_meta.provider
            adapter = self.providers.get(provider_name)
            if not adapter:
                continue

            start_time = time.perf_counter()
            try:
                res = adapter.json_output(messages=messages, schema=schema, model=model_meta.model_name)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                cost = self._calculate_cost(
                    50, 50, model_meta.input_token_price, model_meta.output_token_price
                )
                self._log_usage(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    model_name=model_meta.model_name,
                    provider=provider_name,
                    prompt_tokens=50,
                    completion_tokens=50,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    status="success",
                )
                return res
            except Exception as e:
                last_error = e
                ModelRegistryManager.update_model_health(db, model_meta.model_name, False)

        raise RuntimeError(f"AI Gateway JSON output failed: {str(last_error)}")
