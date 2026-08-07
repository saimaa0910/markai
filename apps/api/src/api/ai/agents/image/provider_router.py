import os
import time
import random
import logging
import requests
import uuid
import datetime
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from api.models.ai_platform import AIProvider, AIProviderKey, AIProviderHealth
from api.ai.providers.base_provider import ProviderRegistry, BaseProvider

logger = logging.getLogger(__name__)

# Keep circuit breakers globally in memory
_CIRCUIT_BREAKERS: Dict[str, Dict[str, Any]] = {}


class ImageProviderRouter:
    """
    Enterprise smart provider router.
    Resolves capability matching, circuit breakers, retries, and sequential failovers.
    """

    def __init__(self, db: Session, organization_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> None:
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id

    def route_operation(
        self,
        operation: str,  # "generate" | "edit" | "variation" | "upscale"
        prompt: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        mask_bytes: Optional[bytes] = None,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None,
        model: Optional[str] = None,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        cfg_scale: Optional[float] = None,
        steps: Optional[int] = None,
        priority_override: Optional[List[str]] = None,
        scale: float = 2.0,
    ) -> Tuple[bytes, str, str]:
        """
        Executes routing pipeline by filtering providers, checking circuit breakers,
        validating capabilities, and resolving failovers.
        """
        from api.models.membership import OrganizationSettings
        default_row = self.db.query(OrganizationSettings).filter(
            OrganizationSettings.organization_id == self.organization_id,
            OrganizationSettings.namespace == "ai",
            OrganizationSettings.key == "default_image_provider"
        ).first()
        
        from api.ai.agents.image.constants import DEFAULT_PROVIDER_PRIORITY
        routing_priority = list(priority_override or DEFAULT_PROVIDER_PRIORITY)
        if default_row and default_row.value:
            def_val = default_row.value.lower()
            if def_val in routing_priority:
                routing_priority.remove(def_val)
            routing_priority.insert(0, def_val)
            
        if "pollinations" not in routing_priority:
            routing_priority.append("pollinations")

        errors = []
        if seed is None:
            seed = random.randint(1, 10000000)

        for provider_name in routing_priority:
            provider_name = provider_name.lower()
            logger.info("Attempting image %s via provider: %s", operation, provider_name)

            # 1. Circuit Breaker validation
            cb = _CIRCUIT_BREAKERS.get(provider_name)
            if cb and cb["failures"] >= 3:
                if time.time() < cb["cooldown_until"]:
                    logger.warning("Provider %s is temporarily blocked (Circuit Breaker active). Skipping.", provider_name)
                    continue
                else:
                    _CIRCUIT_BREAKERS.pop(provider_name, None)

            # 2. Get provider adapter from registry
            provider_instance = ProviderRegistry.get_provider(provider_name)
            if not provider_instance:
                logger.warning("Provider %s is not registered in ProviderRegistry. Skipping.", provider_name)
                continue

            # 3. Match Capabilities
            caps = provider_instance.capabilities()
            cap_map = {
                "generate": "supports_generation",
                "edit": "supports_editing",
                "variation": "supports_variation",
                "upscale": "supports_upscale",
            }
            req_cap = cap_map.get(operation, f"supports_{operation}")
            if not caps.get(req_cap, False):
                logger.warning("Provider %s does not support operation '%s' (cap: %s). Skipping.", provider_name, operation, req_cap)
                continue

            # 4. Resolve Credentials/Key status
            api_key = self._get_key(provider_name)
            if provider_name != "pollinations" and not api_key:
                logger.warning("Provider %s API Key not configured. Skipping.", provider_name)
                continue

            provider_instance.api_key = api_key

            # 5. Check health check status in DB
            db_prov = self.db.scalars(
                select(AIProvider).where(func.lower(AIProvider.name) == provider_name)
            ).first()
            if db_prov:
                health_log = self.db.scalars(
                    select(AIProviderHealth)
                    .where(AIProviderHealth.provider_id == db_prov.id)
                    .order_by(AIProviderHealth.last_checked.desc())
                ).first()
                if health_log and not health_log.is_healthy:
                    # Skip if last check was within 5 minutes
                    time_diff = datetime.datetime.utcnow() - health_log.last_checked.replace(tzinfo=None)
                    if time_diff.total_seconds() < 300:
                        logger.warning("Provider %s is marked unhealthy in database logs. Skipping.", provider_name)
                        continue

            # 6. Execute call with retry loop
            latency_ms = 0
            start_time = time.perf_counter()
            success = False
            result_bytes = None
            resolved_model = model or "default"

            for attempt in range(1, 4):
                try:
                    if operation == "generate":
                        result_bytes = provider_instance.generate(
                            prompt=prompt,
                            width=width,
                            height=height,
                            negative_prompt=negative_prompt,
                            seed=seed,
                            model=model,
                            cfg_scale=cfg_scale,
                            steps=steps
                        )
                    elif operation == "edit":
                        # If image_bytes is missing, attempt placeholder mock
                        img_in = image_bytes or b""
                        mask_in = mask_bytes
                        result_bytes = provider_instance.edit(
                            image_bytes=img_in,
                            prompt=prompt,
                            mask_bytes=mask_in,
                            seed=seed,
                            model=model
                        )
                    elif operation == "variation":
                        img_in = image_bytes or b""
                        result_bytes = provider_instance.variation(
                            image_bytes=img_in,
                            seed=seed,
                            model=model
                        )
                    elif operation == "upscale":
                        img_in = image_bytes or b""
                        result_bytes = provider_instance.upscale(
                            image_bytes=img_in,
                            scale=scale
                        )

                    if result_bytes:
                        success = True
                        latency_ms = int((time.perf_counter() - start_time) * 1000)
                        _CIRCUIT_BREAKERS.pop(provider_name, None)
                        break
                except Exception as e:
                    logger.warning("Provider %s attempt %d failed: %s", provider_name, attempt, e)
                    time.sleep(1.5 ** attempt)

            if success and result_bytes:
                # Log health to DB
                if db_prov:
                    new_health = AIProviderHealth(
                        provider_id=db_prov.id,
                        latency=float(latency_ms),
                        is_healthy=True,
                        last_checked=datetime.datetime.utcnow()
                    )
                    self.db.add(new_health)
                    self.db.commit()

                # Telemetry reporting
                from api.core.metrics_registry import ai_requests_total, ai_request_latency_seconds
                try:
                    ai_requests_total.labels(
                        organization_id=str(self.organization_id),
                        provider=provider_name,
                        model=resolved_model,
                        status="success"
                    ).inc()
                    ai_request_latency_seconds.labels(
                        organization_id=str(self.organization_id),
                        provider=provider_name,
                        model=resolved_model,
                        layer="provider"
                    ).observe(latency_ms / 1000.0)
                except Exception:
                    pass

                return result_bytes, provider_name, resolved_model
            else:
                # Trigger circuit breaker count
                cb_record = _CIRCUIT_BREAKERS.setdefault(provider_name, {"failures": 0, "cooldown_until": 0})
                cb_record["failures"] += 1
                cb_record["cooldown_until"] = time.time() + 600

                # Log failure to health logs
                if db_prov:
                    new_health = AIProviderHealth(
                        provider_id=db_prov.id,
                        latency=0.0,
                        is_healthy=False,
                        last_checked=datetime.datetime.utcnow(),
                        error_message=f"All attempts failed."
                    )
                    self.db.add(new_health)
                    self.db.commit()

                errors.append(f"{provider_name}: All attempts failed.")

        raise RuntimeError(f"All image routing providers failed. Errors: {'; '.join(errors)}")

    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None,
        model: Optional[str] = None,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        priority_override: Optional[List[str]] = None,
        cfg_scale: Optional[float] = None,
        steps: Optional[int] = None,
    ) -> Tuple[bytes, str, str]:
        """Backward compatible generate wrapper."""
        return self.route_operation(
            operation="generate",
            prompt=prompt,
            width=width,
            height=height,
            style=style,
            model=model,
            seed=seed,
            negative_prompt=negative_prompt,
            priority_override=priority_override,
            cfg_scale=cfg_scale,
            steps=steps
        )

    def _get_key(self, provider_name: str) -> Optional[str]:
        """Resolves active API Key via environment overrides or database configurations."""
        env_var_name = f"{provider_name.upper()}_API_KEY"
        if env_var_name == "GOOGLE_API_KEY":
            env_var_name = "GEMINI_API_KEY"
        elif env_var_name == "ANTHROPIC_API_KEY":
            env_var_name = "CLAUDE_API_KEY"

        env_val = os.getenv(env_var_name)
        if env_val:
            return env_val

        # Database lookup
        from api.core.encryption import decrypt_key
        prov = self.db.scalars(
            select(AIProvider).where(func.lower(AIProvider.name) == provider_name.lower())
        ).first()
        if not prov:
            return None

        # User key
        if self.user_id:
            key_record = self.db.scalars(
                select(AIProviderKey).where(
                    AIProviderKey.provider_id == prov.id,
                    AIProviderKey.organization_id == self.organization_id,
                    AIProviderKey.user_id == self.user_id,
                    AIProviderKey.is_active == True
                )
            ).first()
            if key_record:
                try:
                    return decrypt_key(key_record.api_key)
                except Exception:
                    pass

        # Organization key
        key_record = self.db.scalars(
            select(AIProviderKey).where(
                AIProviderKey.provider_id == prov.id,
                AIProviderKey.organization_id == self.organization_id,
                AIProviderKey.user_id == None,
                AIProviderKey.is_active == True
            )
        ).first()
        if key_record:
            try:
                return decrypt_key(key_record.api_key)
            except Exception:
                pass

        return None
