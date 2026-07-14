import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.ai.registry.manager import ModelRegistryManager


class ModelRouter:
    def route(
        self,
        db: Session,
        request_type: str,
        organization_id: Optional[uuid.UUID] = None,
    ) -> List[AIModelRegistry]:
        """
        Evaluate routing rules and return an ordered list of candidate models.
        The first model in the list is the primary selection; remaining models
        serve as fallback choices.
        """
        # Ensure default models are seeded in the database
        ModelRegistryManager.seed_default_models(db)

        # 1. Search for custom tenant-specific routing rule overrides
        rule = None
        if organization_id:
            rule = db.scalars(
                select(AIRoutingRule).where(
                    and_(
                        AIRoutingRule.request_type == request_type,
                        AIRoutingRule.organization_id == organization_id,
                        AIRoutingRule.is_active == True,
                    )
                )
            ).first()

        # 2. Search for system-wide routing rule overrides if no tenant rule is set
        if not rule:
            rule = db.scalars(
                select(AIRoutingRule).where(
                    and_(
                        AIRoutingRule.request_type == request_type,
                        AIRoutingRule.organization_id == None,
                        AIRoutingRule.is_active == True,
                    )
                )
            ).first()

        candidates = []
        if rule and rule.model and rule.model.is_healthy:
            candidates.append(rule.model)

        # 3. Append remaining healthy models sorted by priority as backups
        all_active = ModelRegistryManager.get_active_models(db, request_type)
        for m in all_active:
            if m not in candidates:
                candidates.append(m)

        # 4. Global fail-safe: if no model found, return any healthy chat model
        if not candidates:
            fallback_query = select(AIModelRegistry).where(
                and_(
                    AIModelRegistry.is_healthy == True,
                    AIModelRegistry.supports_streaming == True,
                )
            )
            candidates = list(db.scalars(fallback_query).all())

        return candidates
