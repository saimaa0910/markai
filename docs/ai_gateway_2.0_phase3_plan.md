# AI Gateway 2.0: Phase 3 (Prompt Library Management) - Implementation Plan

This plan details **Phase 3** of Viptant's AI Gateway 2.0.

---

## 1. Clean Architecture Mapping

We build prompt service logic, update prompt validation schemas, and update routing handlers:

```
[Application Layer]  ai/routes/       # Routes mapping update operations
                     ai/schemas/      # PromptUpdate validation card
                     ai/services/     # PromptService version manager
```

---

## 2. Version Control & History Trace

Implement standard incremental history mapping:
*   Updating a prompt creates a new row with `version = latest + 1` instead of modifying existing values.
*   Retain old versions in the database for audit/rollback logs.

---

## 3. API endpoints

*   `POST /` (create V1)
*   `POST /{name}/update` (create new version)
*   `GET /` (list latest versions)
*   `GET /{name}` (get latest version)
*   `GET /{name}/history` (get history records)
*   `DELETE /{name}` (delete prompt family)

---

## 4. Verification Plan

*   **Automated tests**: Verify prompt library version creation, update rollback fallback values, listing latest versions, and deleting families in `tests/test_ai_gateway_phase3.py`.
