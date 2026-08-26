# EAIMOS AI GATEWAY — USAGE & COST AUDIT

**Target:** `apps/api/src/api/ai/gateway/coordinator.py`, `apps/api/src/api/routes/ai.py`, `apps/api/src/api/models/ai_usage.py`, `apps/api/src/api/models/ai_platform.py`.

---

## 1. Usage & Cost Tracking Architecture

The AI Gateway implements token consumption tracking, cost attribution, and tenant capacity enforcement across all AI requests:

```
[Inference Completes] ──► [Token Extraction (Prompt + Completion)]
                                   │
                                   ▼
                       [_calculate_cost() via Model Pricing]
                                   │
                                   ▼
        ┌──────────────────────────┴──────────────────────────┐
        │                                                     │
        ▼                                                     ▼
[Postgres Insertion]                                  [Tenant Quota Deduction]
- AITokenUsage (Tokens, Latency, Model)               - AIOrgLimit.credit_used += cost
- AIRequest (Trace, Duration, Status)                 - AIQuotaUsage.daily_tokens += tokens
- AICost (USD, Breakdown)                             - AIQuotaUsage.daily_spend += cost
        │
        ▼
[Prometheus Counters]
- ai_requests_total
- ai_token_usage_total
- ai_cost_usd_total
```

---

## 2. Detailed Audit Findings

### 2.1 Real-Time Cost Calculation (`coordinator.py:269-281`)
- **Pricing Model**: Prices are stored in `AIModelRegistry` as `input_token_price` and `output_token_price` per **1,000,000 tokens**.
- **Formula**:
  $$\text{Cost} = \left(\frac{\text{prompt\_tokens}}{1,000,000} \times \text{input\_price}\right) + \left(\frac{\text{completion\_tokens}}{1,000,000} \times \text{output\_price}\right)$$
- **Precision**: Uses Python `Decimal` arithmetic rounded to 6 decimal places.
- **Audit Verdict**: `✅ COMPLETE` (Accurate calculation matching cloud provider billing models).

### 2.2 Token Usage Logging & Idempotency (`coordinator.py:283-373`)
- **Tables Updated**: `AITokenUsage`, `AIRequest`, `AIUsage`, `AICost`.
- **Idempotency Protection**: Checks `request_id` in `AITokenUsage` before inserting to prevent duplicate billing on retry loops or connection resets.
- **Audit Verdict**: `✅ COMPLETE`

### 2.3 Organization Budget & Credit Limits (`coordinator.py:640-674`)
- **Limit Table**: `AIOrgLimit` (`credit_limit`, `credit_used`, `rpm_limit`, `tpm_limit`).
- **Enforcement**: Before executing inference, `AIGateway` checks:
  ```python
  if org_limit.credit_limit > Decimal("0.0") and org_limit.credit_used >= org_limit.credit_limit:
      raise ValueError("Organization AI credit limit exceeded.")
  ```
- **Audit Verdict**: `✅ COMPLETE`

### 2.4 Simulated / Dummy Data Injections (`ai.py:1074-1130`)
- **Finding**: Function `seed_dummy_usages(db, organization_id)` in `apps/api/src/api/routes/ai.py` automatically generates **120 fake `AITokenUsage` records** spanning the last 14 days if the table contains 0 rows for that organization.
- **Invocation**: Triggered in `GET /ai/analytics/` (`ai.py:2758`).
- **Risk**: In a production enterprise deployment, new organizations viewing their analytics tab will see simulated token consumption and costs instead of an empty state.
- **Audit Verdict**: `🟡 STATIC/HARDCODED` / `🟠 MOCKED/SIMULATED`

### 2.5 Standalone Cost Tracker Dead Code (`apps/api/src/api/ai/cost/cost_tracker.py`)
- **Finding**: File `cost_tracker.py` contains hardcoded pricing dictionary `MODEL_PRICING` and defaults `{"prompt": 0.000002, "completion": 0.000006}`.
- **Audit Verdict**: `🟡 STATIC/HARDCODED` (Unused dead code; `AIGateway` uses dynamic database prices from `AIModelRegistry`).

---

## 3. Summary Assessment

| Component | Status | Code Location | Finding |
|---|---|---|---|
| Token Accounting | `✅ COMPLETE` | `coordinator.py:283-373` | Prompt, completion, total tokens recorded per request. |
| Cost Calculation | `✅ COMPLETE` | `coordinator.py:269-281` | Dynamic pricing formula based on `AIModelRegistry`. |
| Credit Enforcement | `✅ COMPLETE` | `coordinator.py:640-674` | Hard cutoff on `AIOrgLimit.credit_limit`. |
| Usage Seeder | `🟠 MOCKED/SIMULATED` | `ai.py:1074-1130` | Seeds 120 fake usage rows on empty tables. |
| Standalone Cost Tracker | `🟡 STATIC/HARDCODED` | `cost_tracker.py` | Unused legacy class with hardcoded static rates. |
