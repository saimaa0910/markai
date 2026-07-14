import uuid
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from api.models.ai_registry import AIModelRegistry, AIRoutingRule


class ModelRegistryManager:
    @staticmethod
    def seed_default_models(db: Session) -> None:
        """
        Seed standard default models if the registry is empty.
        """
        existing = db.scalars(select(AIModelRegistry)).first()
        if existing:
            return

        defaults = [
            # Groq Low Latency Models
            AIModelRegistry(
                provider="groq",
                model_name="llama3-70b-8192",
                context_window=8192,
                supports_streaming=True,
                supports_json=True,
                input_token_price=Decimal("0.5900"),
                output_token_price=Decimal("0.7900"),
                latency=Decimal("0.15"),
                priority=10,
                is_healthy=True,
            ),
            AIModelRegistry(
                provider="groq",
                model_name="llama3-8b-8192",
                context_window=8192,
                supports_streaming=True,
                supports_json=True,
                input_token_price=Decimal("0.0500"),
                output_token_price=Decimal("0.1000"),
                latency=Decimal("0.08"),
                priority=9,
                is_healthy=True,
            ),
            # OpenAI Models
            AIModelRegistry(
                provider="openai",
                model_name="gpt-4o-mini",
                context_window=128000,
                supports_streaming=True,
                supports_vision=True,
                supports_json=True,
                supports_tool_calling=True,
                input_token_price=Decimal("0.1500"),
                output_token_price=Decimal("0.6000"),
                latency=Decimal("0.35"),
                priority=9,
                is_healthy=True,
            ),
            AIModelRegistry(
                provider="openai",
                model_name="text-embedding-3-small",
                context_window=8192,
                supports_embeddings=True,
                input_token_price=Decimal("0.0200"),
                output_token_price=Decimal("0.0000"),
                latency=Decimal("0.10"),
                priority=10,
                is_healthy=True,
            ),
            # Claude Models
            AIModelRegistry(
                provider="anthropic",
                model_name="claude-3-5-sonnet-20240620",
                context_window=200000,
                supports_streaming=True,
                supports_vision=True,
                supports_json=True,
                supports_tool_calling=True,
                input_token_price=Decimal("3.0000"),
                output_token_price=Decimal("15.0000"),
                latency=Decimal("0.90"),
                priority=10,
                is_healthy=True,
            ),
            # Gemini Models
            AIModelRegistry(
                provider="google",
                model_name="gemini-1.5-flash",
                context_window=1048576,
                supports_streaming=True,
                supports_vision=True,
                supports_json=True,
                input_token_price=Decimal("0.0750"),
                output_token_price=Decimal("0.3000"),
                latency=Decimal("0.50"),
                priority=10,
                is_healthy=True,
            ),
        ]

        for item in defaults:
            db.add(item)
        db.commit()

        # Seed standard default routing rules matching the models
        # Grab Groq, OpenAI Embeddings, Gemini Vision, Claude JSON
        models = {m.model_name: m for m in defaults}

        rules = [
            AIRoutingRule(request_type="chat", model_registry_id=models["llama3-70b-8192"].id),
            AIRoutingRule(request_type="content", model_registry_id=models["llama3-70b-8192"].id),
            AIRoutingRule(request_type="embeddings", model_registry_id=models["text-embedding-3-small"].id),
            AIRoutingRule(request_type="vision", model_registry_id=models["gemini-1.5-flash"].id),
            AIRoutingRule(request_type="json", model_registry_id=models["claude-3-5-sonnet-20240620"].id),
        ]
        for r in rules:
            db.add(r)
        db.commit()

    @staticmethod
    def get_active_models(
        db: Session, request_type: Optional[str] = None
    ) -> List[AIModelRegistry]:
        """
        Query database to return all active and healthy models sorted by priority.
        Optionally filter by capabilities requested by the specific task type.
        """
        query = select(AIModelRegistry).where(AIModelRegistry.is_healthy == True)

        if request_type == "embeddings":
            query = query.where(AIModelRegistry.supports_embeddings == True)
        elif request_type == "vision":
            query = query.where(AIModelRegistry.supports_vision == True)
        elif request_type == "json":
            query = query.where(AIModelRegistry.supports_json == True)

        query = query.order_by(AIModelRegistry.priority.desc())
        return list(db.scalars(query).all())

    @staticmethod
    def update_model_health(db: Session, model_name: str, is_healthy: bool) -> None:
        """
        Update the health status of a model in the registry database.
        """
        model = db.scalars(
            select(AIModelRegistry).where(AIModelRegistry.model_name == model_name)
        ).first()
        if model:
            model.is_healthy = is_healthy
            db.commit()
