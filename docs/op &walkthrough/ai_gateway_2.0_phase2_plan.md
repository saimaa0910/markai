# AI Gateway 2.0: Phase 2 (Provider Adapters, Model Registry, Router) - Implementation Plan

This plan details **Phase 2** of Viptant's AI Gateway 2.0.

---

## 1. Clean Architecture Mapping

We build provider infrastructure adapters, model registry, and router engine:

```
[Application Layer]  ai/router/       # ModelRouter rules engine
                     ai/registry/     # ModelRegistry manager
                     ai/gateway/      # Gateway client orchestrator
                          ↓
[Infrastructure]     ai/providers/    # Provider Adapter subclasses (HTTP calls via httpx)
```

---

## 2. Adapter Pattern & Base Provider Interface

Implement standard `BaseLLMProvider` contract class. Define methods:
*   `chat(messages, model, temperature, **kwargs)`
*   `stream(messages, model, temperature, **kwargs)`
*   `embeddings(text, model)`
*   `vision(prompt, image_url, model)`
*   `json_output(messages, schema, model)`
*   `health()`

---

## 3. Centralized Model Registry

`ModelRegistryManager` performs automatic seeding of default models and routing overrides (system-wide and tenant-scoped) on first startup.

---

## 4. Model Router Engine & Coordinator

*   **Model Router**: Inspects task capabilities and returns candidates with priority fallback paths.
*   **Gateway Coordinator**: Consolidates routing list, executes adapters, calculates dollar costs, logs audits, and triggers fallback updates.

---

## 5. Verification Plan

*   **Automated tests**: Verify seeding, routing, cost logging, and rates failure fallback in `tests/test_ai_gateway_phase2.py`.
