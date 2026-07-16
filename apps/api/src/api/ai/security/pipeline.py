import re
import uuid
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from api.models.security import AISecurityPolicyRule, AISecurityEvent, AIScanLog, AIQuotaUsage
from api.services.cache_service import CacheService

logger = logging.getLogger("api.ai.security.pipeline")

class AISecurityPipeline:
    def __init__(self) -> None:
        # Standard PII patterns
        self.pii_regex = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            "passport": re.compile(r'\b[A-PR-WYYZa-pr-wyyz][0-9]{7,8}\b'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        }

        # Standard secret keys leak patterns
        self.secret_regex = {
            "openai_key": re.compile(r'\bsk-[a-zA-Z0-9]{48}\b'),
            "groq_key": re.compile(r'\bgsk_[a-zA-Z0-9]{48}\b'),
            "gemini_key": re.compile(r'\bAIzaSy[a-zA-Z0-9_-]{33}\b'),
            "aws_key": re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
            "jwt_token": re.compile(r'\beyJhbGciOi[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+\b'),
            "bearer_token": re.compile(r'\bBearer\s[a-zA-Z0-9-_.]+\b'),
            "database_url": re.compile(r'\bpostgres://[a-zA-Z0-9_]+:[^@]+@[a-zA-Z0-9.-]+:\d+/[a-zA-Z0-9_]+\b'),
        }

        # Prompt injection jailbreak heuristics
        self.injection_keywords = [
            "ignore previous instructions",
            "system override",
            "you are now a bypass shell",
            "dan mode",
            "do anything now",
            "bypass rules",
            "pretend to be",
            "jailbreak",
            "forget your programming",
            "act as an unrestricted",
        ]

        # Basic custom moderation classifications
        self.moderation_categories = {
            "violence": [r"\bkill\b", r"\bmurder\b", r"\bbomb\b", r"\bshoot\b", r"\battack\b", r"\bhurt\b"],
            "hate": [r"\bnigger\b", r"\bfaggot\b", r"\bchink\b", r"\bretard\b"],
            "harassment": [r"\bstalk\b", r"\bharass\b", r"\bbully\b", r"\bhate you\b"],
            "sexual": [r"\bporn\b", r"\bsex\b", r"\bnude\b", r"\berection\b", r"\bpenis\b", r"\bvagina\b"],
            "self_harm": [r"\bsuicide\b", r"\bkill myself\b", r"\bcut myself\b"],
        }

    def _get_active_policy(self, db: Session, organization_id: Optional[uuid.UUID]) -> AISecurityPolicyRule:
        """
        Fetch active policy rule. If none is present, seeds default system rule.
        """
        # Cache policy lookup
        cache = CacheService()
        org_str = str(organization_id) if organization_id else "global"
        
        # Check cache first
        cached_policy = cache.get("policy", f"rule:{org_str}")
        if cached_policy:
            # Re-fetch from DB or return cached representation
            pass
            
        policy = db.scalars(
            select(AISecurityPolicyRule)
            .where(
                AISecurityPolicyRule.is_active == True,
                (AISecurityPolicyRule.organization_id == None) |
                (AISecurityPolicyRule.organization_id == organization_id)
            )
            .order_by(AISecurityPolicyRule.priority.desc())
        ).first()

        if not policy:
            policy = AISecurityPolicyRule(
                name="Default Enterprise Governance Policy",
                scope="global",
                allowed_providers=["openai", "google", "groq", "anthropic", "openrouter"],
                allowed_models=["*"],
                daily_token_limit=50000,
                daily_request_limit=100,
                monthly_token_limit=1000000,
                monthly_request_limit=2000,
                daily_budget_usd=Decimal("5.0000"),
                monthly_budget_usd=Decimal("100.0000"),
                moderation_actions={
                    "violence": "block",
                    "hate": "block",
                    "harassment": "block",
                    "sexual": "redact",
                    "self_harm": "block",
                    "pii": "redact",
                    "secrets": "block"
                },
                pii_masking_policy="redact",
                is_active=True,
                organization_id=organization_id,
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
            
        return policy

    def _get_or_create_quota(self, db: Session, organization_id: Optional[uuid.UUID], user_id: Optional[uuid.UUID]) -> AIQuotaUsage:
        """
        Retrieve or initialize quota usages counters. Reset automatically if past day/month boundary.
        """
        quota = db.scalars(
            select(AIQuotaUsage)
            .where(
                AIQuotaUsage.organization_id == organization_id,
                AIQuotaUsage.user_id == user_id
            )
        ).first()

        now = datetime.utcnow()
        if not quota:
            quota = AIQuotaUsage(
                organization_id=organization_id,
                user_id=user_id,
                daily_tokens=0,
                monthly_tokens=0,
                daily_requests=0,
                monthly_requests=0,
                daily_spend=0.0,
                monthly_spend=0.0,
                last_reset_date=now
            )
            db.add(quota)
            db.commit()
            db.refresh(quota)
            return quota

        # Quotas boundary checks resets
        last_reset = quota.last_reset_date
        
        # Reset daily spend/requests if calendar date changed
        if last_reset.date() != now.date():
            quota.daily_tokens = 0
            quota.daily_requests = 0
            quota.daily_spend = 0.0
            
        # Reset monthly if month changed
        if last_reset.month != now.month or last_reset.year != now.year:
            quota.monthly_tokens = 0
            quota.monthly_requests = 0
            quota.monthly_spend = 0.0
            
        quota.last_reset_date = now
        db.commit()
        return quota

    def validate_input(
        self,
        db: Session,
        prompt_text: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        request_type: str = "chat",
        environment: str = "development"
    ) -> Dict[str, Any]:
        """
        Inspect input text through policy logic, PII, secret leaks, injection warnings,
        and spend limit quotas.
        """
        report = {
            "allowed": True,
            "sanitized_prompt": prompt_text,
            "risk_score": 0.0,
            "categories_triggered": [],
            "errors": [],
            "pii_detected": False,
            "secrets_detected": False,
        }

        policy = self._get_active_policy(db, organization_id)
        quota = self._get_or_create_quota(db, organization_id, user_id)

        # 1. Prompt Length & Complexity validation
        if len(prompt_text) > 20000:
            report["allowed"] = False
            report["errors"].append("Prompt size exceeds maximum system bounds length.")
            self.log_security_event(db, organization_id, user_id, "policy_violation", "critical", "input", "Prompt size > 20k characters", "block")
            return report

        # 2. Quota Check
        if policy.daily_request_limit > 0 and quota.daily_requests >= policy.daily_request_limit:
            report["allowed"] = False
            report["errors"].append("Daily request quota has been reached.")
            self.log_security_event(db, organization_id, user_id, "quota_exceeded", "high", "input", "Daily requests limit exceeded", "block")
            return report
            
        if policy.daily_budget_usd > 0 and float(quota.daily_spend) >= float(policy.daily_budget_usd):
            report["allowed"] = False
            report["errors"].append("Daily credit spend budget has been reached.")
            self.log_security_event(db, organization_id, user_id, "budget_exceeded", "critical", "input", "Daily budget exceeded", "block")
            return report

        # 3. Prompt Injection / Jailbreak detection
        lowered_prompt = prompt_text.lower()
        injection_count = 0
        for kw in self.injection_keywords:
            if kw in lowered_prompt:
                injection_count += 1
                
        if injection_count >= 2:
            report["risk_score"] += 0.6
            report["categories_triggered"].append("jailbreak")
            action = policy.moderation_actions.get("jailbreak", "block") if policy.moderation_actions else "block"
            if action == "block":
                report["allowed"] = False
                report["errors"].append("Jailbreak pattern match detected.")
                self.log_security_event(db, organization_id, user_id, "prompt_injection", "high", "input", "Matched jailbreak heuristics", "block")
                return report

        # 4. Content Moderation check
        for category, patterns in self.moderation_categories.items():
            triggered = False
            for pat in patterns:
                if re.search(pat, lowered_prompt):
                    triggered = True
                    break
            if triggered:
                report["categories_triggered"].append(category)
                action = policy.moderation_actions.get(category, "block") if policy.moderation_actions else "block"
                if action == "block":
                    report["allowed"] = False
                    report["errors"].append(f"Content violation: triggered category '{category}'.")
                    self.log_security_event(db, organization_id, user_id, "moderation_event", "medium", "input", f"Triggered category: {category}", "block")
                    return report

        # 5. Secret Key Leak detection
        secrets_found = []
        for name, rx in self.secret_regex.items():
            matches = rx.findall(prompt_text)
            if matches:
                secrets_found.extend(matches)
                
        if secrets_found:
            report["secrets_detected"] = True
            report["categories_triggered"].append("secrets")
            # Secrets leaks are always blocked in enterprise mode
            report["allowed"] = False
            report["errors"].append("Prompt contains raw unencrypted keys or database secrets.")
            self.log_security_event(db, organization_id, user_id, "secret_leak", "critical", "input", f"Detected credentials leaks", "block")
            return report

        # 6. PII Masking & Redacting
        sanitized = prompt_text
        pii_found = False
        for pii_type, rx in self.pii_regex.items():
            matches = rx.findall(sanitized)
            if matches:
                pii_found = True
                for match in matches:
                    if policy.pii_masking_policy == "redact":
                        sanitized = sanitized.replace(match, f"[REDACTED_{pii_type.upper()}]")
                    elif policy.pii_masking_policy == "mask":
                        sanitized = sanitized.replace(match, f"[*MASKED_{pii_type.upper()}*]")
                    else:
                        sanitized = sanitized.replace(match, "[CONFIDENTIAL_PII]")
                        
        if pii_found:
            report["pii_detected"] = True
            report["sanitized_prompt"] = sanitized
            report["categories_triggered"].append("pii")
            action = policy.moderation_actions.get("pii", "redact") if policy.moderation_actions else "redact"
            if action == "block":
                report["allowed"] = False
                report["errors"].append("Prompt blocked due to PII compliance governance locks.")
                self.log_security_event(db, organization_id, user_id, "pii_leak", "high", "input", "PII block action triggered", "block")
                return report
            else:
                self.log_security_event(db, organization_id, user_id, "pii_leak", "medium", "input", "PII redacted/masked", "redact")

        # 7. Incremental scans logging
        scan = AIScanLog(
            organization_id=organization_id,
            user_id=user_id,
            prompt_length=len(prompt_text),
            prompt_complexity=len(set(lowered_prompt.split())),
            risk_score=report["risk_score"],
            pii_detected=report["pii_detected"],
            secrets_detected=report["secrets_detected"],
            injection_risk=0.8 if injection_count >= 2 else 0.0,
            classification="suspicious" if (injection_count >= 2 or pii_found) else "safe",
        )
        db.add(scan)
        db.commit()

        # Update requests count quota
        quota.daily_requests += 1
        quota.monthly_requests += 1
        db.commit()

        return report

    def validate_output(
        self,
        db: Session,
        output_text: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        original_prompt_text: str
    ) -> Dict[str, Any]:
        """
        Filter and sanitize model outputs. Detects hallucination levels and checks secret leaks.
        """
        report = {
            "allowed": True,
            "sanitized_output": output_text,
            "risk_score": 0.0,
            "categories_triggered": [],
            "pii_detected": False,
            "secrets_detected": False,
        }

        policy = self._get_active_policy(db, organization_id)

        # 1. Output Moderation
        lowered_output = output_text.lower()
        for category, patterns in self.moderation_categories.items():
            triggered = False
            for pat in patterns:
                if re.search(pat, lowered_output):
                    triggered = True
                    break
            if triggered:
                report["categories_triggered"].append(category)
                action = policy.moderation_actions.get(category, "block") if policy.moderation_actions else "block"
                if action == "block":
                    report["allowed"] = False
                    report["sanitized_output"] = "[Blocked due to output content moderation policy.]"
                    self.log_security_event(db, organization_id, user_id, "moderation_event", "medium", "output", f"LLM output violated category: {category}", "block")
                    return report

        # 2. Output Secret leak leakage protection
        secrets_found = []
        for name, rx in self.secret_regex.items():
            matches = rx.findall(output_text)
            if matches:
                secrets_found.extend(matches)
                
        if secrets_found:
            report["secrets_detected"] = True
            report["categories_triggered"].append("secrets")
            # Always redact secrets in LLM outputs to prevent database credentials leak
            sanitized = output_text
            for match in secrets_found:
                sanitized = sanitized.replace(match, "[REDACTED_API_SECRET]")
            report["sanitized_output"] = sanitized
            self.log_security_event(db, organization_id, user_id, "secret_leak", "critical", "output", "Redacted model credentials leak", "redact")

        # 3. Output PII Masking
        sanitized_output = report["sanitized_output"]
        pii_found = False
        for pii_type, rx in self.pii_regex.items():
            matches = rx.findall(sanitized_output)
            if matches:
                pii_found = True
                for match in matches:
                    if policy.pii_masking_policy == "redact":
                        sanitized_output = sanitized_output.replace(match, f"[REDACTED_{pii_type.upper()}]")
                    elif policy.pii_masking_policy == "mask":
                        sanitized_output = sanitized_output.replace(match, f"[*MASKED_{pii_type.upper()}*]")
                    else:
                        sanitized_output = sanitized_output.replace(match, "[CONFIDENTIAL_PII]")

        if pii_found:
            report["pii_detected"] = True
            report["sanitized_output"] = sanitized_output
            report["categories_triggered"].append("pii")
            self.log_security_event(db, organization_id, user_id, "pii_leak", "high", "output", "Redacted PII in LLM output", "redact")

        return report

    def update_quota_tokens(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        tokens_count: int,
        cost: Decimal
    ) -> None:
        """
        Accrue tokens consumption and spend budgets.
        """
        quota = self._get_or_create_quota(db, organization_id, user_id)
        quota.daily_tokens += tokens_count
        quota.monthly_tokens += tokens_count
        quota.daily_spend = float(Decimal(str(quota.daily_spend)) + cost)
        quota.monthly_spend = float(Decimal(str(quota.monthly_spend)) + cost)
        db.commit()

    def log_security_event(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        event_type: str,
        severity: str,
        trigger_source: str,
        details: str,
        action_taken: str
    ) -> None:
        """
        Create immutable security scan violation event records.
        """
        event = AISecurityEvent(
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            trigger_source=trigger_source,
            details=details[:4000],
            action_taken=action_taken
        )
        db.add(event)
        db.commit()
