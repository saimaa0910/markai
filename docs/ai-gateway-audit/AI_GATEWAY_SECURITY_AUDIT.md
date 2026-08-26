# EAIMOS AI GATEWAY — SECURITY & GOVERNANCE AUDIT

**Target:** `apps/api/src/api/ai/security/pipeline.py` (`AISecurityPipeline`), `apps/api/src/api/models/security_platform.py`, `apps/api/src/api/services/rate_limit_service.py`.

---

## 1. Security Architecture Overview

The AI Gateway enforces bidirectional security inspection on all incoming prompts and outgoing model responses:

```
[Client Request]
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│           AISecurityPipeline.validate_input()                │
│  1. Prompt Length Check (<20,000 characters)                 │
│  2. Daily Request & Daily Spend Quota Check                  │
│  3. Jailbreak & Prompt Injection Heuristic Scan              │
│  4. Content Moderation Category Filter (Hate, Violence, etc.)│
│  5. Raw Secret & API Key Leak Detection (Always Block)       │
│  6. PII Masking / Redacting (Email, Phone, SSN, CC, etc.)    │
│  7. Security Audit Log (`AIScanLog`, `AISecurityEvent`)      │
└──────────────────────────────┬───────────────────────────────┘
                               │ (If allowed & sanitized)
                               ▼
                    [AIGateway LLM Inference]
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│           AISecurityPipeline.validate_output()               │
│  1. Content Moderation Violation Check                       │
│  2. Secret & Credential Leak Redaction                       │
│  3. Model Output PII Redaction / Masking                     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
                       [Client Response]
```

---

## 2. Detailed Security Capabilities & Vulnerability Analysis

### 2.1 PII Masking & Redaction
- **Regex Patterns Covered**:
  - Emails: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
  - US Phone Numbers: `(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}`
  - Social Security Numbers (SSN): `\b\d{3}-\d{2}-\d{4}\b`
  - Credit Cards: `(?:\d{4}[-\s]?){3}\d{4}`
  - Passports: `[A-PR-WYYZa-pr-wyyz][0-9]{7,8}`
  - IP Addresses: `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`
- **Actions Supported**: `redact` (`[REDACTED_EMAIL]`), `mask` (`[*MASKED_EMAIL*]`), `block`.
- **Audit Verdict**: `✅ COMPLETE`

### 2.2 Secret & Credential Leakage Prevention
- **Patterns Covered**: OpenAI API keys (`sk-...`), Groq API keys (`gsk_...`), Google Gemini keys (`AIzaSy...`), AWS access keys (`AKIA...`), JWT tokens (`eyJhbGciOi...`), Bearer tokens, PostgreSQL connection URLs (`postgres://...`).
- **Policy**:
  - Input: Prompt is immediately blocked and logged as critical severity.
  - Output: LLM response has all matching secret substrings replaced with `[REDACTED_API_SECRET]`.
- **Audit Verdict**: `✅ COMPLETE`

### 2.3 Prompt Injection & Jailbreak Heuristics
- **Heuristics**: Keyword density matching (`"ignore previous instructions"`, `"system override"`, `"dan mode"`, `"do anything now"`, `"bypass rules"`, `"forget your programming"`).
- **Vulnerability Finding**: Simple regex and keyword matching can be bypassed by advanced adversarial techniques (Base64 encoding, ROT13, multilingual prompt injections, role-play obfuscation).
- **Audit Verdict**: `⚠️ PARTIAL` (Requires LLM guardrail classifier in addition to static heuristics).

### 2.4 Quota & Rate Limiting Enforcement
- **Quotas (`AIQuotaUsage`)**: Tracks `daily_tokens`, `monthly_tokens`, `daily_requests`, `monthly_requests`, `daily_spend`, `monthly_spend` with automatic calendar date reset. `✅ COMPLETE`
- **Rate Limiting (`RateLimitService`)**: Implements sliding window rate limiting.
  - **Vulnerability / Performance Bottleneck**: `RateLimitLog` writes every attempt to PostgreSQL rather than high-performance Redis sorted sets (`ZADD`/`ZREMRANGEBYSCORE`), creating write lock contention under high concurrency.
- **Audit Verdict**: `⚠️ PARTIAL`

### 2.5 Provider API Key Encryption at Rest
- **Encryption**: Uses cryptography Fernet symmetric encryption (`ENCRYPTION_KEY` in environment settings).
- **Masking**: Keys returned to clients in API responses are masked (`sk-...1234`).
- **Audit Verdict**: `✅ COMPLETE`

---

## 3. Summary of Security Risks & Remediations

1. **Adversarial Prompt Injection**: Static keywords are vulnerable to encoding tricks. Recommend integrating a dedicated prompt classifier (e.g. Llama Guard or NeMo Guardrails).
2. **PostgreSQL Rate Limit Write Contention**: Under 20,000 concurrent users, logging every rate limit attempt to PostgreSQL will degrade database performance. Offload to Redis.
3. **Regex PII False Positives**: Static regex for IP addresses matches version strings (e.g. `1.2.3.4`). Consider contextual NER models for advanced PII scanning.
