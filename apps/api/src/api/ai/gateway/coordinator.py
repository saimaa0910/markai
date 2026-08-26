import os
import uuid
import time
import logging
from typing import List, Dict, Any, Optional, Generator
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select

logger = logging.getLogger(__name__)

from api.ai.router.engine import ModelRouter
from api.ai.registry.manager import ModelRegistryManager
from api.models.ai_usage import AITokenUsage
from api.models.ai_registry import AIModelRegistry
from api.models.ai_platform import AIProvider, AIProviderKey, AIRequest, AIUsage, AICost, AIOrgLimit
from api.core.encryption import decrypt_key
from api.services.cache_service import CacheService
from api.ai.security.pipeline import AISecurityPipeline


class AIGateway:
    def __init__(self) -> None:
        self.router = ModelRouter()
        from api.ai.providers.openai import OpenAIProvider
        from api.ai.providers.groq import GroqProvider
        from api.ai.providers.openrouter import OpenRouterProvider
        from api.ai.providers.claude import ClaudeProvider
        from api.ai.providers.gemini import GeminiProvider
        from api.ai.providers.deepseek import DeepSeekProvider
        from api.ai.providers.mistral import MistralProvider
        from api.ai.providers.ollama import OllamaProvider
        self.providers = {
            "openai": OpenAIProvider(),
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "anthropic": ClaudeProvider(),
            "google": GeminiProvider(),
            "deepseek": DeepSeekProvider(),
            "mistral": MistralProvider(),
            "ollama": OllamaProvider(),
        }
        # Per-provider circuit breaker state (P2-7):
        # provider -> {"failures": int, "open_until": float, "retry_after": float, "opened_at": float}
        self._breaker = {}

    # ── Circuit breaker (P2-7 & P3-1) ─────────────────────────────────────────
    def _breaker_threshold(self) -> int:
        return 5  # consecutive failures before opening the circuit

    def _breaker_cooldown(self, retry_after: Optional[float] = None) -> float:
        return (retry_after or 60.0) + 5.0

    def _breaker_is_open(self, provider: str) -> Optional[float]:
        """Return seconds remaining until circuit closes, or None if closed."""
        from api.core.metrics_registry import (
            ai_provider_circuit_breaker_state,
            ai_provider_circuit_breaker_open_time_seconds,
            ai_provider_circuit_breaker_transitions_total
        )
        prov_key = provider.lower()
        state = self._breaker.get(prov_key)
        if not state:
            try:
                ai_provider_circuit_breaker_state.labels(provider=prov_key).set(0)
                ai_provider_circuit_breaker_open_time_seconds.labels(provider=prov_key).set(0)
            except Exception:
                pass
            return None

        now = time.time()
        open_until = state.get("open_until", 0)
        if open_until == 0:
            return None

        if open_until > now:
            try:
                ai_provider_circuit_breaker_state.labels(provider=prov_key).set(2)
                opened_at = state.get("opened_at", now)
                ai_provider_circuit_breaker_open_time_seconds.labels(provider=prov_key).set(max(0.0, now - opened_at))
            except Exception:
                pass
            return open_until - now

        # Cooldown elapsed: reset and transition to closed
        self._breaker.pop(prov_key, None)
        try:
            ai_provider_circuit_breaker_state.labels(provider=prov_key).set(0)
            ai_provider_circuit_breaker_open_time_seconds.labels(provider=prov_key).set(0)
            ai_provider_circuit_breaker_transitions_total.labels(provider=prov_key, from_state="open", to_state="closed").inc()
        except Exception:
            pass
        return None

    def _breaker_record_failure(self, provider: str, retry_after: Optional[float] = None) -> None:
        from api.core.metrics_registry import (
            ai_provider_circuit_breaker_failures_total,
            ai_provider_circuit_breaker_state,
            ai_provider_circuit_breaker_transitions_total
        )
        prov_key = provider.lower()
        try:
            ai_provider_circuit_breaker_failures_total.labels(provider=prov_key).inc()
        except Exception:
            pass

        state = self._breaker.setdefault(prov_key, {"failures": 0, "open_until": 0, "retry_after": 0, "opened_at": 0})
        state["failures"] += 1
        if retry_after is not None:
            state["retry_after"] = float(retry_after)
        if state["failures"] >= self._breaker_threshold():
            now = time.time()
            state["opened_at"] = now
            state["open_until"] = now + self._breaker_cooldown(
                state.get("retry_after") or retry_after
            )
            try:
                ai_provider_circuit_breaker_state.labels(provider=prov_key).set(2)
                ai_provider_circuit_breaker_transitions_total.labels(provider=prov_key, from_state="closed", to_state="open").inc()
            except Exception:
                pass
            logger.warning(f"Circuit breaker opened for provider '{provider}' after "
                           f"{state['failures']} consecutive failures.")

    def _breaker_record_success(self, provider: str) -> None:
        from api.core.metrics_registry import (
            ai_provider_circuit_breaker_state,
            ai_provider_circuit_breaker_open_time_seconds,
            ai_provider_circuit_breaker_transitions_total
        )
        prov_key = provider.lower()
        if prov_key in self._breaker:
            self._breaker.pop(prov_key, None)
            try:
                ai_provider_circuit_breaker_state.labels(provider=prov_key).set(0)
                ai_provider_circuit_breaker_open_time_seconds.labels(provider=prov_key).set(0)
                ai_provider_circuit_breaker_transitions_total.labels(provider=prov_key, from_state="open", to_state="closed").inc()
            except Exception:
                pass
        else:
            try:
                ai_provider_circuit_breaker_state.labels(provider=prov_key).set(0)
                ai_provider_circuit_breaker_open_time_seconds.labels(provider=prov_key).set(0)
            except Exception:
                pass

    def _extract_retry_after(self, exc: Exception) -> Optional[float]:
        """Parse Retry-After from a provider 429 HTTPStatusError."""
        resp = getattr(exc, "response", None)
        if resp is None:
            return None
        if getattr(resp, "status_code", None) != 429:
            return None
        ra = resp.headers.get("Retry-After") if resp.headers else None
        if not ra:
            return None
        try:
            return float(ra)
        except (TypeError, ValueError):
            return None

    def _get_provider_adapter(
        self, db: Session, provider_name: str, organization_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Any:
        """
        Dynamically lookup the decrypted custom API Key:
        1. Checks User-level keys
        2. Checks Organization-level (Workspace) keys
        3. Falls back to system environment variables
        """
        from sqlalchemy import func
        prov_name_lower = provider_name.lower()

        db_prov = db.scalars(
            select(AIProvider).where(func.lower(AIProvider.name) == prov_name_lower)
        ).first()

        db_key = None
        # 1. User-level credentials check — only the owning user may read their own key
        if user_id:
            from api.models.iam import OAuthAccount  # just to ensure import context
            db_key = db.scalars(
                select(AIProviderKey)
                .join(AIProvider)
                .where(
                    func.lower(AIProvider.name) == prov_name_lower,
                    AIProviderKey.user_id == user_id,
                    AIProviderKey.is_active == True,
                    # Ensure the caller is the same user who owns the key
                    AIProviderKey.user_id == user_id,
                )
            ).first()

        # 2. Org-level credentials check
        if not db_key and organization_id:
            db_key = db.scalars(
                select(AIProviderKey)
                .join(AIProvider)
                .where(
                    func.lower(AIProvider.name) == prov_name_lower,
                    AIProviderKey.organization_id == organization_id,
                    AIProviderKey.user_id == None,
                    AIProviderKey.is_active == True,
                )
            ).first()

        decrypted_key = None
        if db_key and db_key.api_key:
            try:
                decrypted_key = decrypt_key(db_key.api_key)
            except Exception:
                pass
        elif db_prov and db_prov.config and db_prov.config.get("api_key"):
            try:
                decrypted_key = decrypt_key(db_prov.config["api_key"])
            except Exception:
                decrypted_key = db_prov.config.get("api_key")

        # Adapter class mapping
        from api.ai.providers.openai import OpenAIProvider
        from api.ai.providers.groq import GroqProvider
        from api.ai.providers.openrouter import OpenRouterProvider
        from api.ai.providers.claude import ClaudeProvider
        from api.ai.providers.gemini import GeminiProvider
        from api.ai.providers.deepseek import DeepSeekProvider
        from api.ai.providers.mistral import MistralProvider
        from api.ai.providers.ollama import OllamaProvider

        adapters = {
            "openai": OpenAIProvider,
            "groq": GroqProvider,
            "openrouter": OpenRouterProvider,
            "anthropic": ClaudeProvider,
            "google": GeminiProvider,
            "deepseek": DeepSeekProvider,
            "mistral": MistralProvider,
            "ollama": OllamaProvider,
        }

        adapter_cls = adapters.get(prov_name_lower)
        if not adapter_cls:
            raise ValueError(f"Unknown or unsupported AI provider: '{provider_name}'")
        base_url = db_prov.base_url if db_prov else None

        env_key_names = {
            "google": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "ollama": "OLLAMA_API_KEY",
        }
        target_env = env_key_names.get(prov_name_lower, f"{prov_name_lower.upper()}_API_KEY")
        active_key = decrypted_key or os.getenv(target_env)

        provider_instance = self.providers.get(prov_name_lower)
        if provider_instance:
            provider_instance.api_key = active_key
            if hasattr(provider_instance, "base_url") and base_url:
                provider_instance.base_url = base_url
            return provider_instance

        if adapter_cls in (OpenAIProvider, DeepSeekProvider, MistralProvider, OllamaProvider):
            return adapter_cls(api_key=active_key, base_url=base_url)
        return adapter_cls(api_key=active_key)

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
        request_id: Optional[str] = None,
    ) -> None:
        """
        Write execution metrics log audit to database usage table.
        Also triggers structured JSON logging, trace collection, and Prometheus reporting.

        Idempotency (P2-4): when a request_id is provided, an existing success/failure
        record for the same request_id is not duplicated, preventing double-charge on
        retries and fallback paths.
        """
        if request_id:
            existing_usage = db.scalars(
                select(AITokenUsage).where(
                    AITokenUsage.request_id == request_id,
                    AITokenUsage.status == status,
                )
            ).first()
            if existing_usage:
                logger.debug(f"Duplicate usage record skipped for request_id={request_id}")
                return

        usage_old = AITokenUsage(
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
            request_id=request_id,
        )
        db.add(usage_old)

        req = AIRequest(
            organization_id=organization_id,
            user_id=user_id,
            provider=provider,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status=status
        )
        db.add(req)

        usage_new = AIUsage(
            organization_id=organization_id,
            user_id=user_id,
            provider=provider,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message
        )
        db.add(usage_new)

        if status == "success" and cost_usd > 0:
            cost = AICost(
                organization_id=organization_id,
                provider=provider,
                model=model_name,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                cost_usd=cost_usd
            )
            db.add(cost)

        db.commit()

        # --- Phase 1D Observability Extensions ---
        # 1. Structured JSON Logging using structlog
        try:
            import structlog
            struct_logger = structlog.get_logger("api.ai.gateway.coordinator")
            log_method = struct_logger.info if status == "success" else struct_logger.error
            log_method(
                "AI Gateway execution event",
                organization_id=str(organization_id),
                user_id=str(user_id),
                provider=provider,
                model=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=float(cost_usd),
                latency_ms=latency_ms,
                status=status,
                error_message=error_message,
            )
        except Exception:
            pass

        # 2. Database Logs table insertion (ai_logs)
        try:
            from api.models.observability import AILog
            from api.core.telemetry import get_current_trace_and_span_ids
            import structlog
            
            trace_id, span_id = get_current_trace_and_span_ids()
            ctx = structlog.contextvars.get_contextvars()
            correlation_id = ctx.get("correlation_id")
            request_id = ctx.get("request_id")
            
            db_log = AILog(
                trace_id=trace_id,
                span_id=span_id,
                correlation_id=correlation_id,
                request_id=request_id,
                organization_id=organization_id,
                user_id=user_id,
                level="INFO" if status == "success" else "ERROR",
                logger="api.ai.gateway.coordinator",
                message=f"AI Request to {provider}/{model_name} resolved with status {status}",
                payload={
                    "provider": provider,
                    "model": model_name,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost_usd": float(cost_usd),
                    "latency_ms": latency_ms,
                    "error_message": error_message
                }
            )
            db.add(db_log)
            db.commit()
        except Exception:
            pass

        # 3. Database Traces table insertion (ai_traces)
        try:
            from datetime import datetime, timedelta
            from api.models.observability import AITrace
            from api.core.telemetry import get_current_trace_and_span_ids
            trace_id, span_id = get_current_trace_and_span_ids()
            
            if trace_id:
                # Approximate start time from latency
                start_dt = datetime.utcnow() - timedelta(milliseconds=latency_ms)
                db_trace = AITrace(
                    trace_id=trace_id,
                    span_id=span_id,
                    name=f"gateway.{provider}.{model_name}",
                    organization_id=organization_id,
                    user_id=user_id,
                    start_time=start_dt,
                    end_time=datetime.utcnow(),
                    duration_ms=latency_ms,
                    status=status,
                    error_message=error_message,
                    attributes={
                        "provider": provider,
                        "model": model_name,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "cost_usd": float(cost_usd)
                    }
                )
                db.add(db_trace)
                db.commit()
        except Exception:
            pass

        # 4. Prometheus metrics reporting
        try:
            from api.core.metrics_registry import (
                ai_requests_total, ai_request_latency_seconds,
                ai_token_usage_total, ai_cost_usd_total, ai_errors_total
            )
            
            org_str = str(organization_id) if organization_id else "system"
            
            ai_requests_total.labels(
                organization_id=org_str,
                provider=provider,
                model=model_name,
                status=status
            ).inc()
            
            ai_request_latency_seconds.labels(
                organization_id=org_str,
                provider=provider,
                model=model_name,
                layer="provider"
            ).observe(latency_ms / 1000.0)
            
            if prompt_tokens > 0:
                ai_token_usage_total.labels(
                    organization_id=org_str,
                    provider=provider,
                    model=model_name,
                    type="prompt"
                ).inc(prompt_tokens)
                
            if completion_tokens > 0:
                ai_token_usage_total.labels(
                    organization_id=org_str,
                    provider=provider,
                    model=model_name,
                    type="completion"
                ).inc(completion_tokens)
                
            if cost_usd > 0:
                ai_cost_usd_total.labels(
                    organization_id=org_str,
                    provider=provider,
                    model=model_name
                ).inc(float(cost_usd))
                
            if status != "success":
                ai_errors_total.labels(
                    organization_id=org_str,
                    provider=provider,
                    model=model_name,
                    error_code="PROVIDER_ERROR",
                    layer="provider"
                ).inc()
        except Exception:
            pass

        # 5. Alert dispatching for errors
        if status != "success":
            try:
                from api.services.alert_engine import AlertEngine
                msg = f"AI Provider call failed for {provider}/{model_name} in organization {organization_id}. Error: {error_message}"
                AlertEngine.trigger_alert(
                    db=db,
                    alert_type="PROVIDER_ERROR",
                    message=msg,
                    severity="warning",
                    organization_id=organization_id
                )
            except Exception:
                pass

    def _log_routing(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        request_type: str,
        strategy_used: str,
        selected_provider: str,
        selected_model: str,
        fallback_count: int,
        retry_count: int,
        latency_ms: int,
        cost_usd: Decimal,
        prompt_tokens: int,
        completion_tokens: int,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log routing choices in full details to Postgres/SQLite.
        """
        from api.models.router import AIRoutingLog
        log = AIRoutingLog(
            organization_id=organization_id,
            user_id=user_id,
            request_type=request_type,
            strategy_used=strategy_used,
            selected_provider=selected_provider,
            selected_model=selected_model,
            fallback_count=fallback_count,
            retry_count=retry_count,
            latency_ms=latency_ms,
            cost_usd=float(cost_usd),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            success=success,
            error_message=error_message[:4000] if error_message else None,
        )
        db.add(log)
        db.commit()

    def _log_failover(
        self,
        db: Session,
        organization_id: uuid.UUID,
        failed_provider: str,
        failed_model: str,
        fallback_provider: str,
        fallback_model: str,
        error_message: str,
        attempts: int,
    ) -> None:
        """
        Log provider failover incidents.
        Also increments failover metrics and dispatches failover alerts.
        """
        from api.models.router import AIFailoverEvent
        event = AIFailoverEvent(
            organization_id=organization_id,
            failed_provider=failed_provider,
            failed_model=failed_model,
            fallback_provider=fallback_provider,
            fallback_model=fallback_model,
            error_message=error_message[:4000],
            retry_attempts=attempts,
        )
        db.add(event)
        db.commit()

        # Update Prometheus Metrics
        try:
            from api.core.metrics_registry import ai_failovers_total
            org_str = str(organization_id) if organization_id else "system"
            ai_failovers_total.labels(
                organization_id=org_str,
                failed_provider=failed_provider,
                failed_model=failed_model,
                fallback_provider=fallback_provider,
                fallback_model=fallback_model
            ).inc()
        except Exception:
            pass

        # Trigger Failover Alert Incident
        try:
            from api.services.alert_engine import AlertEngine
            msg = (
                f"Failover Event: Provider '{failed_provider}' model '{failed_model}' failed. "
                f"Automatically failing over to '{fallback_provider}' model '{fallback_model}'. "
                f"Error: {error_message}"
            )
            AlertEngine.report_incident(
                db=db,
                component="gateway",
                service="ai_router",
                severity="warning",
                root_cause=msg,
                organization_id=organization_id
            )
        except Exception:
            pass

    def _check_and_seed_limit(self, db: Session, organization_id: uuid.UUID) -> None:
        """
        Verify the organization limits, seeding default limit block if absent.
        Raises RuntimeError if the budget has been exceeded.
        """
        org_limit = db.scalars(
            select(AIOrgLimit).where(AIOrgLimit.organization_id == organization_id)
        ).first()

        if not org_limit:
            org_limit = AIOrgLimit(
                organization_id=organization_id,
                credit_limit=100.00,
                credit_used=0.000000,
                rpm_limit=60,
                tpm_limit=50000,
            )
            db.add(org_limit)
            db.commit()
            db.refresh(org_limit)

        if float(org_limit.credit_used) >= float(org_limit.credit_limit):
            raise RuntimeError("Organization has exceeded its allocated AI credit budget limit.")

    def _update_credit_usage(self, db: Session, organization_id: uuid.UUID, cost: Decimal) -> None:
        """
        Increment the credit usage of the organization.
        """
        org_limit = db.scalars(
            select(AIOrgLimit).where(AIOrgLimit.organization_id == organization_id)
        ).first()
        if org_limit:
            org_limit.credit_used = float(Decimal(str(org_limit.credit_used)) + cost)
            db.commit()

    def _validate_request(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        model_meta: AIModelRegistry,
    ) -> None:
        """
        Pre-validation checking capabilities, activation status, and credit caps.
        """
        self._check_and_seed_limit(db, organization_id)
        
        if not model_meta.is_healthy:
            raise ValueError(f"Selected model '{model_meta.model_name}' is currently marked unhealthy.")

    def chat(
        self,
        db: Session,
        messages: List[Dict[str, str]],
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        temperature: float = 0.7,
        rag_enabled: bool = False,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Orchestrate chat execution with automated routing, retry, and failover.
        """
        self._check_and_seed_limit(db, organization_id)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # 1. AI Security Pipeline Validation (Input Scanner)
        sec_pipeline = AISecurityPipeline()
        user_contents = [m["content"] for m in messages if m["role"] == "user"]
        scan_target = "\n".join(user_contents) if user_contents else ""
        
        sec_report = sec_pipeline.validate_input(
            db=db,
            prompt_text=scan_target,
            organization_id=organization_id,
            user_id=user_id,
            request_type="chat",
        )
        
        if not sec_report["allowed"]:
            raise RuntimeError(f"Request blocked by AI Security Pipeline: {', '.join(sec_report['errors'])}")
            
        if sec_report["pii_detected"] and sec_report["sanitized_prompt"]:
            # Mask user content in final messages payload
            for m in reversed(messages):
                if m["role"] == "user":
                    m["content"] = sec_report["sanitized_prompt"]
                    break

        retrieved_chunks = []
        rag_query_text = None
        if rag_enabled and messages:
            user_msgs = [m for m in messages if m["role"] == "user"]
            if user_msgs:
                rag_query_text = user_msgs[-1]["content"]
                from api.services.knowledge_service import KnowledgeService
                retrieved_chunks = KnowledgeService.query_similar_chunks(
                    db=db,
                    query_text=rag_query_text,
                    organization_id=organization_id,
                    user_id=user_id,
                    limit=3,
                )
                if retrieved_chunks:
                    context_str = "\n---\n".join(c.content for c in retrieved_chunks)
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

        ModelRegistryManager.seed_default_models(db)

        # Extract optional routing parameter overrides
        requested_model_name = kwargs.pop("model_name", None)
        strategy = kwargs.pop("strategy", None)
        task_type = kwargs.pop("task_type", None)
        required_features = kwargs.pop("required_features", None)
        min_context_window = kwargs.pop("min_context_window", None)
        environment = kwargs.pop("environment", None)
        load_balancer = kwargs.pop("load_balancer", None)

        candidates = []
        if requested_model_name:
            db_model = db.scalars(
                select(AIModelRegistry).where(
                    AIModelRegistry.model_name == requested_model_name
                )
            ).first()
            if db_model:
                candidates = [db_model]

        if not candidates:
            candidates = self.router.route(
                db=db,
                request_type="chat",
                organization_id=organization_id,
                user_id=user_id,
                strategy=strategy,
                task_type=task_type,
                required_features=required_features,
                min_context_window=min_context_window,
                environment=environment,
                load_balancer=load_balancer,
            )

        if not candidates:
            raise RuntimeError("No healthy models available in registry.")

        last_error = None
        fallback_count = 0
        retry_count = 0
        max_retries = 3

        for idx, model_meta in enumerate(candidates):
            provider_name = model_meta.provider
            
            cache = CacheService()
            if cache.get("blacklist", f"model:{model_meta.model_name}"):
                fallback_count += 1
                continue

            try:
                cache.set("load", model_meta.model_name, str(int(cache.get("load", model_meta.model_name) or 0) + 1))
            except Exception:
                pass

            for attempt in range(max_retries):
                start_time = time.perf_counter()
                try:
                    open_after = self._breaker_is_open(provider_name)
                    if open_after is not None:
                        raise RuntimeError(
                            f"Provider '{provider_name}' circuit breaker open for {open_after:.0f}s"
                        )

                    self._validate_request(db, organization_id, user_id, model_meta)
                    adapter = self._get_provider_adapter(db, provider_name, organization_id, user_id=user_id)
                    if not adapter:
                        raise ValueError(f"Provider adapter '{provider_name}' not available.")

                    res = adapter.chat(
                        messages=messages,
                        model=model_meta.model_name,
                        temperature=temperature,
                        **kwargs,
                    )
                    
                    # 2. AI Security Pipeline Output validation
                    output_text = res.get("content", "")
                    sec_out_report = sec_pipeline.validate_output(
                        db=db,
                        output_text=output_text,
                        organization_id=organization_id,
                        user_id=user_id,
                        original_prompt_text=scan_target
                    )
                    
                    if not sec_out_report["allowed"]:
                        raise RuntimeError("Response blocked by AI Security Pipeline output checks.")
                        
                    if sec_out_report["pii_detected"] or sec_out_report["secrets_detected"]:
                        res["content"] = sec_out_report["sanitized_output"]

                    latency_ms = res.get("latency_ms", int((time.perf_counter() - start_time) * 1000))
                    prompt_tokens = res.get("prompt_tokens", 0)
                    completion_tokens = res.get("completion_tokens", 0)
                    cost = self._calculate_cost(
                        prompt_tokens,
                        completion_tokens,
                        model_meta.input_token_price,
                        model_meta.output_token_price,
                    )

                    self._update_credit_usage(db, organization_id, cost)
                    
                    # Update metrics and quotas counters
                    sec_pipeline.update_quota_tokens(db, organization_id, user_id, prompt_tokens + completion_tokens, cost)
                    
                    try:
                        cache.set("load", model_meta.model_name, str(max(0, int(cache.get("load", model_meta.model_name) or 0) - 1)))
                    except Exception:
                        pass

                    self._breaker_record_success(provider_name)

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
                        request_id=request_id,
                    )

                    self._log_routing(
                        db=db,
                        organization_id=organization_id,
                        user_id=user_id,
                        request_type="chat",
                        strategy_used=strategy or "balanced",
                        selected_provider=provider_name,
                        selected_model=model_meta.model_name,
                        fallback_count=idx,
                        retry_count=retry_count,
                        latency_ms=latency_ms,
                        cost_usd=cost,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        success=True
                    )

                    res["cost_usd"] = cost
                    res["model"] = model_meta.model_name
                    res["provider"] = provider_name

                    if retrieved_chunks and "content" in res and rag_query_text:
                        from api.services.vector_store import VectorStore
                        query_embedding = self.embeddings(
                            db=db, text=rag_query_text, organization_id=organization_id, user_id=user_id
                        )
                        sources_md = "\n\n---\n**Sources & Context Retrieved:**\n"
                        for chunk_idx, chunk in enumerate(retrieved_chunks):
                            sim_score = VectorStore._cosine_similarity(query_embedding, chunk.embedding)
                            sim_pct = int(sim_score * 100)
                            doc_title = chunk.document.title if chunk.document else "Untitled Document"
                            doc_type = chunk.document.file_type if chunk.document else "txt"
                            short_snippet = chunk.content[:150].replace('\n', ' ')
                            sources_md += f"- **{doc_title}** ({doc_type.upper()}) — *Similarity: {sim_pct}%*\n"
                            sources_md += f"  - Chunk {chunk_idx+1}: \"{short_snippet}...\"\n"
                        res["content"] = f"{res['content']}{sources_md}"

                    return res

                except Exception as e:
                    last_error = e
                    retry_count += 1
                    retry_after = self._extract_retry_after(e)
                    self._breaker_record_failure(provider_name, retry_after)
                    time.sleep((2 ** attempt) * 0.1 + (retry_after or 0))

            try:
                cache.set("blacklist", f"model:{model_meta.model_name}", "failed", ttl=300)
                cache.set("load", model_meta.model_name, str(max(0, int(cache.get("load", model_meta.model_name) or 0) - 1)))
                ModelRegistryManager.update_model_health(db, model_meta.model_name, False)
            except Exception:
                pass

            self._log_usage(
                db=db,
                organization_id=organization_id,
                user_id=user_id,
                model_name=model_meta.model_name,
                provider=provider_name,
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=Decimal("0.0"),
                latency_ms=0,
                status="failure",
                error_message=str(last_error),
                request_id=request_id,
            )

            if idx < len(candidates) - 1:
                next_model = candidates[idx + 1]
                self._log_failover(
                    db=db,
                    organization_id=organization_id,
                    failed_provider=provider_name,
                    failed_model=model_meta.model_name,
                    fallback_provider=next_model.provider,
                    fallback_model=next_model.model_name,
                    error_message=str(last_error),
                    attempts=retry_count,
                )

        self._log_routing(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            request_type="chat",
            strategy_used=strategy or "balanced",
            selected_provider="none",
            selected_model="none",
            fallback_count=fallback_count,
            retry_count=retry_count,
            latency_ms=0,
            cost_usd=Decimal("0.0"),
            prompt_tokens=0,
            completion_tokens=0,
            success=False,
            error_message=str(last_error)
        )
        from api.core.config import settings
        _ = settings  # environment no longer gates a fabricated fallback (P1-1/P2-1)
        err_str = str(last_error) if last_error else "Unknown error occurred"
        if ("image" in err_str.lower() or "vision" in err_str.lower()) and ("support" in err_str.lower() or "unsupported" in err_str.lower()):
            err_str = "The selected model does not support image input. Please select a vision-capable model (e.g. GPT-4o, Claude 3.5 Sonnet) or use text-only mode."
        raise RuntimeError(f"AI Gateway failed to execute chat requests: {err_str}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        organization_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[Session] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Executes a simple generation query, resolving DB session and default IDs if not provided.
        """
        from api.database.session import SessionLocal
        
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            if organization_id is None:
                from api.models.organization import Organization
                org = db.query(Organization).first()
                organization_id = org.id if org else uuid.uuid4()
            if user_id is None:
                from api.models.user import User
                usr = db.query(User).first()
                user_id = usr.id if usr else uuid.uuid4()
                
            messages = [{"role": "user", "content": prompt}]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
                
            res = self.chat(
                db=db,
                messages=messages,
                organization_id=organization_id,
                user_id=user_id,
                temperature=temperature,
                model_name=model_name,
                **kwargs
            )
            
            return {
                "output": res.get("content", ""),
                "provider": res.get("provider", "unknown"),
                "tokens_used": res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
                "cost_usd": float(res.get("cost_usd", 0.0)),
            }
        finally:
            if close_db:
                db.close()

    def stream(
        self,
        db: Session,
        messages: List[Dict[str, str]],
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        temperature: float = 0.7,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute streaming chat completion yielding chunk dictionaries.
        """
        self._check_and_seed_limit(db, organization_id)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        sec_pipeline = AISecurityPipeline()
        user_contents = [m["content"] for m in messages if m["role"] == "user"]
        scan_target = "\n".join(user_contents) if user_contents else ""
        
        sec_report = sec_pipeline.validate_input(
            db=db,
            prompt_text=scan_target,
            organization_id=organization_id,
            user_id=user_id,
            request_type="chat",
        )
        if not sec_report["allowed"]:
            raise RuntimeError(f"Request blocked by AI Security Pipeline: {', '.join(sec_report['errors'])}")
        if sec_report["pii_detected"] and sec_report["sanitized_prompt"]:
            for m in reversed(messages):
                if m["role"] == "user":
                    m["content"] = sec_report["sanitized_prompt"]
                    break

        ModelRegistryManager.seed_default_models(db)
        
        requested_model_name = kwargs.pop("model_name", None)
        strategy = kwargs.pop("strategy", None)
        task_type = kwargs.pop("task_type", None)
        required_features = kwargs.pop("required_features", None)
        min_context_window = kwargs.pop("min_context_window", None)
        environment = kwargs.pop("environment", None)
        load_balancer = kwargs.pop("load_balancer", None)

        candidates = []
        if requested_model_name:
            db_model = db.scalars(
                select(AIModelRegistry).where(
                    AIModelRegistry.model_name == requested_model_name
                )
            ).first()
            if db_model:
                candidates = [db_model]

        if not candidates:
            candidates = self.router.route(
                db=db,
                request_type="chat",
                organization_id=organization_id,
                user_id=user_id,
                strategy=strategy,
                task_type=task_type,
                required_features=required_features,
                min_context_window=min_context_window,
                environment=environment,
                load_balancer=load_balancer,
            )

        if not candidates:
            raise RuntimeError("No healthy models available in registry.")

        last_error = None
        fallback_count = 0
        retry_count = 0
        max_retries = 3

        for idx, model_meta in enumerate(candidates):
            provider_name = model_meta.provider
            
            cache = CacheService()
            if cache.get("blacklist", f"model:{model_meta.model_name}"):
                fallback_count += 1
                continue

            try:
                cache.set("load", model_meta.model_name, str(int(cache.get("load", model_meta.model_name) or 0) + 1))
            except Exception:
                pass

            for attempt in range(max_retries):
                start_time = time.perf_counter()
                try:
                    open_after = self._breaker_is_open(provider_name)
                    if open_after is not None:
                        raise RuntimeError(
                            f"Provider '{provider_name}' circuit breaker open for {open_after:.0f}s"
                        )

                    self._validate_request(db, organization_id, user_id, model_meta)
                    adapter = self._get_provider_adapter(db, provider_name, organization_id, user_id=user_id)
                    if not adapter:
                        raise ValueError(f"Provider adapter '{provider_name}' not available.")

                    generator_chunks = adapter.stream(
                        messages=messages,
                        model=model_meta.model_name,
                        temperature=temperature,
                        **kwargs,
                    )

                    content_accum = []
                    usage = {"prompt_tokens": 0, "completion_tokens": 0}
                    for chunk in generator_chunks:
                        if chunk.get("done"):
                            usage = chunk.get("usage") or usage
                            continue
                        if "content" in chunk:
                            content_accum.append(chunk["content"])
                        yield chunk

                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    full_content = "".join(content_accum)
                    
                    # Validate Output
                    sec_out_report = sec_pipeline.validate_output(
                        db=db,
                        output_text=full_content,
                        organization_id=organization_id,
                        user_id=user_id,
                        original_prompt_text=scan_target
                    )
                    if not sec_out_report["allowed"]:
                        raise RuntimeError("Response blocked by AI Security Pipeline output checks.")

                    # Real token accounting from provider usage payload (P2-4)
                    prompt_tokens = usage.get("prompt_tokens") or len(messages[-1]["content"].split()) if messages else 0
                    completion_tokens = usage.get("completion_tokens") or len(full_content.split())
                    cost = self._calculate_cost(
                        prompt_tokens,
                        completion_tokens,
                        model_meta.input_token_price,
                        model_meta.output_token_price,
                    )

                    self._update_credit_usage(db, organization_id, cost)
                    sec_pipeline.update_quota_tokens(db, organization_id, user_id, prompt_tokens + completion_tokens, cost)
                    
                    try:
                        cache.set("load", model_meta.model_name, str(max(0, int(cache.get("load", model_meta.model_name) or 0) - 1)))
                    except Exception:
                        pass

                    self._breaker_record_success(provider_name)

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
                        request_id=request_id,
                    )

                    self._log_routing(
                        db=db,
                        organization_id=organization_id,
                        user_id=user_id,
                        request_type="chat",
                        strategy_used=strategy or "balanced",
                        selected_provider=provider_name,
                        selected_model=model_meta.model_name,
                        fallback_count=idx,
                        retry_count=retry_count,
                        latency_ms=latency_ms,
                        cost_usd=cost,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        success=True
                    )
                    return

                except Exception as e:
                    last_error = e
                    retry_count += 1
                    retry_after = self._extract_retry_after(e)
                    self._breaker_record_failure(provider_name, retry_after)
                    time.sleep((2 ** attempt) * 0.1 + (retry_after or 0))

            try:
                cache.set("blacklist", f"model:{model_meta.model_name}", "failed", ttl=300)
                cache.set("load", model_meta.model_name, str(max(0, int(cache.get("load", model_meta.model_name) or 0) - 1)))
                ModelRegistryManager.update_model_health(db, model_meta.model_name, False)
            except Exception:
                pass

            self._log_usage(
                db=db,
                organization_id=organization_id,
                user_id=user_id,
                model_name=model_meta.model_name,
                provider=provider_name,
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=Decimal("0.0"),
                latency_ms=0,
                status="failure",
                error_message=str(last_error),
                request_id=request_id,
            )

            if idx < len(candidates) - 1:
                next_model = candidates[idx + 1]
                self._log_failover(
                    db=db,
                    organization_id=organization_id,
                    failed_provider=provider_name,
                    failed_model=model_meta.model_name,
                    fallback_provider=next_model.provider,
                    fallback_model=next_model.model_name,
                    error_message=str(last_error),
                    attempts=retry_count,
                )

        from api.core.config import settings
        _ = settings  # environment no longer gates a fabricated fallback (P1-1/P2-1)
        raise RuntimeError(f"AI Gateway streaming failed: {str(last_error)}")

    def embeddings(
        self,
        db: Session,
        text: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> List[float]:
        self._check_and_seed_limit(db, organization_id)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        sec_pipeline = AISecurityPipeline()
        sec_report = sec_pipeline.validate_input(
            db=db,
            prompt_text=text,
            organization_id=organization_id,
            user_id=user_id,
            request_type="embeddings",
        )
        if not sec_report["allowed"]:
            raise RuntimeError(f"Request blocked by AI Security Pipeline: {', '.join(sec_report['errors'])}")
        if sec_report["pii_detected"] and sec_report["sanitized_prompt"]:
            text = sec_report["sanitized_prompt"]

        strategy = kwargs.pop("strategy", None)
        load_balancer = kwargs.pop("load_balancer", None)
        
        candidates = self.router.route(
            db=db, 
            request_type="embeddings", 
            organization_id=organization_id,
            user_id=user_id,
            strategy=strategy,
            load_balancer=load_balancer,
        )
        if not candidates:
            raise RuntimeError("No healthy embeddings models registry available.")

        last_error = None
        fallback_count = 0
        retry_count = 0
        
        for idx, model_meta in enumerate(candidates):
            provider_name = model_meta.provider
            
            cache = CacheService()
            if cache.get("blacklist", f"model:{model_meta.model_name}"):
                fallback_count += 1
                continue

            start_time = time.perf_counter()
            try:
                open_after = self._breaker_is_open(provider_name)
                if open_after is not None:
                    raise RuntimeError(
                        f"Provider '{provider_name}' circuit breaker open for {open_after:.0f}s"
                    )

                self._validate_request(db, organization_id, user_id, model_meta)
                adapter = self._get_provider_adapter(db, provider_name, organization_id, user_id=user_id)
                if not adapter:
                    raise ValueError(f"Provider adapter '{provider_name}' not available.")

                vector = adapter.embeddings(text=text, model=model_meta.model_name)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                cost = self._calculate_cost(
                    len(text.split()), 0, model_meta.input_token_price, model_meta.output_token_price
                )
                self._update_credit_usage(db, organization_id, cost)
                sec_pipeline.update_quota_tokens(db, organization_id, user_id, len(text.split()), cost)

                self._breaker_record_success(provider_name)

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
                    request_id=request_id,
                )
                self._log_routing(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    request_type="embeddings",
                    strategy_used=strategy or "balanced",
                    selected_provider=provider_name,
                    selected_model=model_meta.model_name,
                    fallback_count=idx,
                    retry_count=retry_count,
                    latency_ms=latency_ms,
                    cost_usd=cost,
                    prompt_tokens=len(text.split()),
                    completion_tokens=0,
                    success=True
                )
                return vector
            except Exception as e:
                last_error = e
                retry_count += 1
                retry_after = self._extract_retry_after(e)
                self._breaker_record_failure(provider_name, retry_after)
                try:
                    cache.set("blacklist", f"model:{model_meta.model_name}", "failed", ttl=300)
                except Exception:
                    pass
                if idx < len(candidates) - 1:
                    next_model = candidates[idx + 1]
                    self._log_failover(
                        db=db,
                        organization_id=organization_id,
                        failed_provider=provider_name,
                        failed_model=model_meta.model_name,
                        fallback_provider=next_model.provider,
                        fallback_model=next_model.model_name,
                        error_message=str(last_error),
                        attempts=retry_count,
                    )

        raise RuntimeError(f"AI Gateway embeddings execution failed: {str(last_error)}")

    def vision(
        self,
        db: Session,
        prompt: str,
        image_url: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        self._check_and_seed_limit(db, organization_id)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        sec_pipeline = AISecurityPipeline()
        sec_report = sec_pipeline.validate_input(
            db=db,
            prompt_text=prompt,
            organization_id=organization_id,
            user_id=user_id,
            request_type="vision",
        )
        if not sec_report["allowed"]:
            raise RuntimeError(f"Request blocked by AI Security Pipeline: {', '.join(sec_report['errors'])}")
        if sec_report["pii_detected"] and sec_report["sanitized_prompt"]:
            prompt = sec_report["sanitized_prompt"]

        strategy = kwargs.pop("strategy", None)
        load_balancer = kwargs.pop("load_balancer", None)
        
        candidates = self.router.route(
            db=db,
            request_type="vision",
            organization_id=organization_id,
            user_id=user_id,
            strategy=strategy,
            load_balancer=load_balancer,
        )
        if not candidates:
            raise RuntimeError("No healthy vision models available.")

        last_error = None
        fallback_count = 0
        retry_count = 0
        
        for idx, model_meta in enumerate(candidates):
            provider_name = model_meta.provider
            
            cache = CacheService()
            if cache.get("blacklist", f"model:{model_meta.model_name}"):
                fallback_count += 1
                continue

            start_time = time.perf_counter()
            try:
                open_after = self._breaker_is_open(provider_name)
                if open_after is not None:
                    raise RuntimeError(
                        f"Provider '{provider_name}' circuit breaker open for {open_after:.0f}s"
                    )

                self._validate_request(db, organization_id, user_id, model_meta)
                adapter = self._get_provider_adapter(db, provider_name, organization_id, user_id=user_id)
                if not adapter:
                    raise ValueError(f"Provider adapter '{provider_name}' not available.")

                res = adapter.vision(prompt=prompt, image_url=image_url, model=model_meta.model_name)
                
                # Output scan
                output_text = res.get("content", "")
                sec_out_report = sec_pipeline.validate_output(
                    db=db,
                    output_text=output_text,
                    organization_id=organization_id,
                    user_id=user_id,
                    original_prompt_text=prompt
                )
                if not sec_out_report["allowed"]:
                    raise RuntimeError("Response blocked by AI Security Pipeline output checks.")
                if sec_out_report["pii_detected"] or sec_out_report["secrets_detected"]:
                    res["content"] = sec_out_report["sanitized_output"]

                latency_ms = int((time.perf_counter() - start_time) * 1000)
                cost = self._calculate_cost(
                    100, 100, model_meta.input_token_price, model_meta.output_token_price
                )
                self._update_credit_usage(db, organization_id, cost)
                sec_pipeline.update_quota_tokens(db, organization_id, user_id, 200, cost)

                self._breaker_record_success(provider_name)

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
                    request_id=request_id,
                )
                self._log_routing(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    request_type="vision",
                    strategy_used=strategy or "balanced",
                    selected_provider=provider_name,
                    selected_model=model_meta.model_name,
                    fallback_count=idx,
                    retry_count=retry_count,
                    latency_ms=latency_ms,
                    cost_usd=cost,
                    prompt_tokens=100,
                    completion_tokens=100,
                    success=True
                )
                return res
            except Exception as e:
                last_error = e
                retry_count += 1
                retry_after = self._extract_retry_after(e)
                self._breaker_record_failure(provider_name, retry_after)
                try:
                    cache.set("blacklist", f"model:{model_meta.model_name}", "failed", ttl=300)
                except Exception:
                    pass
                if idx < len(candidates) - 1:
                    next_model = candidates[idx + 1]
                    self._log_failover(
                        db=db,
                        organization_id=organization_id,
                        failed_provider=provider_name,
                        failed_model=model_meta.model_name,
                        fallback_provider=next_model.provider,
                        fallback_model=next_model.model_name,
                        error_message=str(last_error),
                        attempts=retry_count,
                    )

        raise RuntimeError(f"AI Gateway vision execution failed: {str(last_error)}")

    def json_output(
        self,
        db: Session,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        self._check_and_seed_limit(db, organization_id)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        sec_pipeline = AISecurityPipeline()
        user_contents = [m["content"] for m in messages if m["role"] == "user"]
        scan_target = "\n".join(user_contents) if user_contents else ""
        
        sec_report = sec_pipeline.validate_input(
            db=db,
            prompt_text=scan_target,
            organization_id=organization_id,
            user_id=user_id,
            request_type="json",
        )
        if not sec_report["allowed"]:
            raise RuntimeError(f"Request blocked by AI Security Pipeline: {', '.join(sec_report['errors'])}")
        if sec_report["pii_detected"] and sec_report["sanitized_prompt"]:
            for m in reversed(messages):
                if m["role"] == "user":
                    m["content"] = sec_report["sanitized_prompt"]
                    break

        strategy = kwargs.pop("strategy", None)
        load_balancer = kwargs.pop("load_balancer", None)
        
        candidates = self.router.route(
            db=db,
            request_type="json",
            organization_id=organization_id,
            user_id=user_id,
            strategy=strategy,
            load_balancer=load_balancer,
        )
        if not candidates:
            raise RuntimeError("No healthy JSON models available.")

        last_error = None
        fallback_count = 0
        retry_count = 0
        
        for idx, model_meta in enumerate(candidates):
            provider_name = model_meta.provider
            
            cache = CacheService()
            if cache.get("blacklist", f"model:{model_meta.model_name}"):
                fallback_count += 1
                continue

            start_time = time.perf_counter()
            try:
                open_after = self._breaker_is_open(provider_name)
                if open_after is not None:
                    raise RuntimeError(
                        f"Provider '{provider_name}' circuit breaker open for {open_after:.0f}s"
                    )

                self._validate_request(db, organization_id, user_id, model_meta)
                adapter = self._get_provider_adapter(db, provider_name, organization_id, user_id=user_id)
                if not adapter:
                    raise ValueError(f"Provider adapter '{provider_name}' not available.")

                res = adapter.json_output(messages=messages, schema=schema, model=model_meta.model_name)
                
                # Output scan
                sec_out_report = sec_pipeline.validate_output(
                    db=db,
                    output_text=str(res),
                    organization_id=organization_id,
                    user_id=user_id,
                    original_prompt_text=scan_target
                )
                if not sec_out_report["allowed"]:
                    raise RuntimeError("Response blocked by AI Security Pipeline output checks.")

                latency_ms = int((time.perf_counter() - start_time) * 1000)
                cost = self._calculate_cost(
                    50, 50, model_meta.input_token_price, model_meta.output_token_price
                )
                self._update_credit_usage(db, organization_id, cost)
                sec_pipeline.update_quota_tokens(db, organization_id, user_id, 100, cost)

                self._breaker_record_success(provider_name)

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
                    request_id=request_id,
                )
                self._log_routing(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    request_type="json",
                    strategy_used=strategy or "balanced",
                    selected_provider=provider_name,
                    selected_model=model_meta.model_name,
                    fallback_count=idx,
                    retry_count=retry_count,
                    latency_ms=latency_ms,
                    cost_usd=cost,
                    prompt_tokens=50,
                    completion_tokens=50,
                    success=True
                )
                return res
            except Exception as e:
                last_error = e
                retry_count += 1
                retry_after = self._extract_retry_after(e)
                self._breaker_record_failure(provider_name, retry_after)
                try:
                    cache.set("blacklist", f"model:{model_meta.model_name}", "failed", ttl=300)
                except Exception:
                    pass
                if idx < len(candidates) - 1:
                    next_model = candidates[idx + 1]
                    self._log_failover(
                        db=db,
                        organization_id=organization_id,
                        failed_provider=provider_name,
                        failed_model=model_meta.model_name,
                        fallback_provider=next_model.provider,
                        fallback_model=next_model.model_name,
                        error_message=str(last_error),
                        attempts=retry_count,
                    )

        raise RuntimeError(f"AI Gateway JSON output failed: {str(last_error)}")
