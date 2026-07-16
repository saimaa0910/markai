import uuid
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.models.router import AIRoutingPolicy
from api.ai.registry.manager import ModelRegistryManager
from api.services.cache_service import CacheService


class ModelRouter:
    def route(
        self,
        db: Session,
        request_type: str,
        organization_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        strategy: Optional[str] = None,
        task_type: Optional[str] = None,
        required_features: Optional[List[str]] = None,
        min_context_window: Optional[int] = None,
        environment: Optional[str] = None,
        load_balancer: Optional[str] = None,
    ) -> List[AIModelRegistry]:
        """
        Intelligent routing entrypoint evaluating policies, blacklists,
        pricing, latency metrics, and load balancing rules.
        """
        # Ensure default models are seeded in database
        ModelRegistryManager.seed_default_models(db)
        
        # 1. Fetch active models
        models = db.scalars(select(AIModelRegistry).where(AIModelRegistry.is_healthy == True)).all()
        if not models:
            return []

        # 2. Exclude temporarily blacklisted models/providers in Redis cache
        cache = CacheService()
        active_candidates = []
        for m in models:
            if cache.get("blacklist", f"model:{m.model_name}"):
                continue
            if cache.get("blacklist", f"provider:{m.provider}"):
                continue
            active_candidates.append(m)

        # If all healthy models are blacklisted, fallback to standard health list
        if not active_candidates:
            active_candidates = list(models)

        # 3. Evaluate AIRoutingPolicies matching org, env, or task
        policies_query = select(AIRoutingPolicy).where(AIRoutingPolicy.is_active == True)
        if organization_id:
            policies_query = policies_query.where(
                (AIRoutingPolicy.organization_id == None) |
                (AIRoutingPolicy.organization_id == organization_id)
            )
        else:
            policies_query = policies_query.where(AIRoutingPolicy.organization_id == None)
            
        policies = db.scalars(policies_query.order_by(AIRoutingPolicy.priority.desc())).all()
        
        matched_strategy = strategy
        for p in policies:
            if p.request_type != "*" and p.request_type != request_type:
                continue
                
            match = True
            if p.conditions:
                for k, v in p.conditions.items():
                    if k == "task" and task_type != v:
                        match = False
                    if k == "environment" and environment != v:
                        match = False
                    if k == "user_id" and user_id and str(user_id) != str(v):
                        match = False
            if match:
                matched_strategy = p.routing_strategy
                break

        if not matched_strategy:
            matched_strategy = "balanced"

        # 4. Filter candidates based on capabilities & context window requirements
        filtered = []
        for m in active_candidates:
            if request_type != "embeddings" and m.supports_embeddings:
                continue
            if request_type == "vision" and not m.supports_vision:
                continue
            if request_type == "embeddings" and not m.supports_embeddings:
                continue
            if request_type == "json" and not m.supports_json:
                continue
                
            if required_features:
                if "streaming" in required_features and not m.supports_streaming:
                    continue
                if "vision" in required_features and not m.supports_vision:
                    continue
                if "json" in required_features and not m.supports_json:
                    continue
                if "tool_calling" in required_features and not m.supports_tool_calling:
                    continue
                    
            if min_context_window and m.context_window < min_context_window:
                continue
                
            filtered.append(m)

        # Fallback if filtering left no candidates
        if not filtered:
            filtered = active_candidates

        # 5. Sort candidates matching routing strategy
        if matched_strategy == "cheapest":
            filtered.sort(key=lambda x: (x.input_token_price + x.output_token_price))
        elif matched_strategy == "fastest":
            filtered.sort(key=lambda x: x.latency)
        elif matched_strategy == "highest_quality":
            filtered.sort(key=lambda x: x.priority, reverse=True)
        elif matched_strategy == "reasoning":
            filtered.sort(key=lambda x: (0 if "claude" in x.model_name.lower() or "gpt-4" in x.model_name.lower() else 1, -x.priority))
        elif matched_strategy == "coding":
            filtered.sort(key=lambda x: (0 if "gpt-oss" in x.model_name.lower() or "llama-3.3" in x.model_name.lower() else 1, -x.priority))
        elif matched_strategy == "vision":
            filtered.sort(key=lambda x: (0 if x.supports_vision else 1, -x.priority))
        elif matched_strategy == "balanced":
            filtered.sort(key=lambda x: (float(x.input_token_price) * 5.0 + float(x.latency) * 2.0))
        else:
            filtered.sort(key=lambda x: x.priority, reverse=True)

        # 5.5. Apply AIRoutingRule overrides
        if not strategy:
            rule_query = select(AIRoutingRule).where(
                AIRoutingRule.request_type == request_type,
                AIRoutingRule.is_active == True
            )
            if organization_id:
                rule_query = rule_query.where(
                    (AIRoutingRule.organization_id == None) |
                    (AIRoutingRule.organization_id == organization_id)
                )
            else:
                rule_query = rule_query.where(AIRoutingRule.organization_id == None)
                
            rule_query = rule_query.order_by(AIRoutingRule.organization_id.desc())
            db_rules = db.scalars(rule_query).all()
            
            if db_rules:
                rule_model_ids = {r.model_registry_id for r in db_rules}
                matched = [c for c in filtered if c.id in rule_model_ids]
                others = [c for c in filtered if c.id not in rule_model_ids]
                filtered = matched + others

        # 6. Apply load balancing strategy
        lb_mode = load_balancer or "priority"
        return self._load_balance(filtered, lb_mode)

    def _load_balance(self, candidates: List[AIModelRegistry], lb_strategy: str) -> List[AIModelRegistry]:
        if not candidates or len(candidates) <= 1:
            return candidates
            
        cache = CacheService()
        
        if lb_strategy == "round_robin":
            try:
                cnt = int(cache.get("lb", "round_robin_counter") or 0)
            except Exception:
                cnt = 0
            cache.set("lb", "round_robin_counter", str(cnt + 1))
            shift = cnt % len(candidates)
            return candidates[shift:] + candidates[:shift]
            
        elif lb_strategy == "least_loaded":
            def get_load(model_name: str) -> int:
                try:
                    return int(cache.get("load", model_name) or 0)
                except Exception:
                    return 0
            return sorted(candidates, key=lambda x: get_load(x.model_name))
            
        elif lb_strategy == "random":
            import random
            shuffled = list(candidates)
            random.shuffle(shuffled)
            return shuffled
            
        return candidates
