# EAIMOS AI GATEWAY — ROUTING ENGINE AUDIT

**Target:** `apps/api/src/api/ai/router/engine.py` (`ModelRouter`), `apps/api/src/api/routes/router.py`, `apps/api/src/api/models/router.py`

---

## 1. Routing Engine Architecture

The EAIMOS Model Router orchestrates request dispatching across multiple providers using a 6-stage evaluation pipeline:

```
[Incoming Request]
       │
       ▼
1. Fetch Healthy Models (`AIModelRegistry.is_healthy == True`)
       │
       ▼
2. Exclude Redis Blacklisted Models & Providers (`cache.get("blacklist", ...)`)
       │
       ▼
3. Evaluate `AIRoutingPolicy` (Org, Environment, Task, Priority)
       │
       ▼
4. Capability & Context Window Filtering (`streaming`, `vision`, `json`, `tool_calling`, `min_context_window`)
       │
       ▼
5. Sort by Strategy (`cheapest`, `fastest`, `balanced`, `highest_quality`, `reasoning`, `coding`, `auto_offpeak`)
       │
       ▼
6. Apply Load Balancing (`priority`, `round_robin`, `least_loaded`, `random`)
       │
       ▼
[Ordered List of Candidate Models]
```

---

## 2. Detailed Audit by Routing Strategy

| Strategy | Algorithm Implementation | Status | Findings / Risks |
|---|---|---|---|
| **`cheapest`** | `sort(key=lambda x: x.input_token_price + x.output_token_price)` | `✅ COMPLETE` | Accurate token price sorting. If database token prices are `$0.00`, defaults to insertion order. |
| **`fastest`** | `sort(key=lambda x: x.latency)` | `✅ COMPLETE` | Sorts by benchmark latency stored in milliseconds. |
| **`balanced`** | `sort(key=lambda x: float(x.input_token_price) * 5.0 + float(x.latency) * 2.0)` | `✅ COMPLETE` | Weighted formula balancing cost and speed. |
| **`highest_quality`** | `sort(key=lambda x: x.priority, reverse=True)` | `✅ COMPLETE` | Routes to highest priority enterprise model. |
| **`auto_offpeak`** | Checks if UTC hour is between `00:00` and `08:00`. If off-peak, applies `cheapest`; otherwise `balanced`. | `✅ COMPLETE` | Timezone is locked to UTC. |
| **`reasoning`** | `(0 if "claude" in m.model_name or "gpt-4" in m.model_name else 1, -x.priority)` | `🟡 STATIC/HARDCODED` | Hardcoded substring matching fails to automatically capture DeepSeek-R1 or Qwen-2.5 reasoning models. |
| **`coding`** | `(0 if "gpt-oss" in m.model_name or "llama-3.3" in m.model_name else 1, -x.priority)` | `🟡 STATIC/HARDCODED` | Hardcoded substring matching for code models. |
| **`vision`** | `(0 if x.supports_vision else 1, -x.priority)` | `✅ COMPLETE` | Dynamically checks `supports_vision` boolean flag. |

---

## 3. Load Balancing & Resilience Audit

### 3.1 Load Balancing Strategies
1. **`priority` (Default)**: Preserves sorted order based on strategy scoring.
2. **`round_robin`**: Increments `round_robin_counter` in Redis and rotates the candidate array via modulo shifting (`candidates[shift:] + candidates[:shift]`). `✅ COMPLETE`
3. **`least_loaded`**: Reads active in-flight request gauge from Redis `cache.get("load", model_name)` and sorts ascending. `✅ COMPLETE`
4. **`random`**: Executes Python `random.shuffle()` across candidates. `✅ COMPLETE`

### 3.2 Circuit Breaker & Failover Integration
- If a provider adapter fails during `AIGateway.chat()` or `stream()`:
  1. Circuit breaker increments failure count for the provider.
  2. If consecutive failures reach **5**, the provider enters OPEN state for **65 seconds**.
  3. `AIGateway` catches the exception, logs failover telemetry to `AIFailoverEvent`, and iterates to the next candidate model in the list returned by `ModelRouter`.
  4. Up to 3 retry attempts are made with exponential backoff (0.5s, 1.0s, 2.0s).

### 3.3 Critical Routing Findings & Deficiencies
1. **Multi-Worker Circuit Breaker Sync**: Circuit breaker failure tracking is stored in an in-memory dictionary `self._breaker` inside the Python process. In a multi-worker production environment, failure counts are not shared across workers.
2. **Hardcoded Model Tags**: Routing strategies `reasoning` and `coding` rely on static string matching (`"claude"`, `"gpt-4"`, `"gpt-oss"`, `"llama-3.3"`) rather than metadata tags in `AIModelRegistry`.
3. **Automatic Health Benchmark Updates**: While model latency is used in `fastest` and `balanced` sorting, latency values in `AIModelRegistry` are updated on manual health checks rather than continuously calculating an exponentially weighted moving average (EWMA) of live traffic.
