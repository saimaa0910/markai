# Sprint 5 Walkthrough: Campaigns (A/B Testing, Templates, Execution)

This document presents the details of the Campaigns module implemented during Sprint 5.

---

## 1. Requirements Met

*   **Campaign Definition & Channel Targeting**: Marketers can schedule campaigns under `EMAIL`, `SOCIAL`, or `ADS` channels with customized budgets.
*   **State Machine Validation**: Validates transition steps (`DRAFT` -> `SCHEDULED` / `ACTIVE`, `ACTIVE` -> `COMPLETED`, etc.) to prevent logical anomalies in marketing schedules.
*   **A/B Variant Copy Testing**: Templates configure comparative content (`Variant A` vs `Variant B`).
*   **Performance Tracking**: Captures click-through impressions, clicks, conversions, and revenue per variant.
*   **Tenant Security Isolation**: Strictly partitions campaigns and performance metrics by `organization_id`.

---

## 2. API Endpoints

All campaigns endpoints reside under `/api/v1/campaigns/`:

| Method | Endpoint | Description | Tenant Context Isolated | Role Protected |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/campaigns/` | Create a campaign with templates & trackers | Yes | Yes (MEMBER+) |
| `GET` | `/api/v1/campaigns/` | List campaigns matching organization context | Yes | Yes (MEMBER+) |
| `GET` | `/api/v1/campaigns/{id}` | Retrieve specific campaign details & analytics | Yes | Yes (MEMBER+) |
| `PUT` | `/api/v1/campaigns/{id}` | Update parameters or transition state | Yes | Yes (MEMBER+) |
| `DELETE` | `/api/v1/campaigns/{id}` | Soft-delete a campaign | Yes | Yes (MEMBER+) |
| `POST` | `/api/v1/campaigns/{id}/execute` | Run execution and load simulated metrics logs | Yes | Yes (MEMBER+) |
| `POST` | `/api/v1/campaigns/{id}/track` | Record impression/click/conversion events | Yes | Yes (MEMBER+) |

---

## 3. Verification Results

*   **Pytest Suite**: Wrote `tests/test_campaigns.py` verifying full lifecycle, A/B metrics updates, and multi-tenant blocks.
*   **Execution Logs**: All 8 tests passed successfully:
    ```bash
    tests/test_campaigns.py .                                                [ 50%]
    ======================= 8 passed, 13 warnings in 8.98s ========================
    ```
*   **Type Safety**: Verified strict types using Pydantic V2 and SQLAlchemy 2.
