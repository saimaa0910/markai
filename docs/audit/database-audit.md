# Database Audit & Schema Analysis

## Audit Overview

This audit evaluates the database schema implementation across all 32 SQLAlchemy model files in `apps/api/src/api/models/`.

---

## Audit Summary Table

| Category | Status | Count | Risk Level |
| :--- | :--- | :--- | :--- |
| **Missing Composite Indexes** | Detected | 4 Table Areas | Medium |
| **Potential N+1 Query Patterns** | Detected | 3 Route / Service Locations | High |
| **Unused / Underutilized Tables** | Detected | 2 Tables | Low |
| **Foreign Key Constraints in SQLite** | Advisory | Dev SQLite Mode | Low |

---

## 1. Missing Index Recommendations

### `ai_usage_logs` Table ([ai_usage.py](file:///d:/markai/apps/api/src/api/models/ai_usage.py))
- **Current State**: Single column PK `id`.
- **Query Pattern**: Analytics queries query usage totals grouped by `organization_id` and filtered by date range (`created_at`).
- **Recommendation**: Add composite index on `(organization_id, created_at)`.

### `knowledge_chunks` Table ([knowledge.py](file:///d:/markai/apps/api/src/api/models/knowledge.py))
- **Current State**: Foreign key on `document_id`.
- **Query Pattern**: RAG Engine retrieves all chunks belonging to a document ordered by `chunk_index`.
- **Recommendation**: Add composite index on `(document_id, chunk_index)`.

### `agent_executions` Table ([agent.py](file:///d:/markai/apps/api/src/api/models/agent.py))
- **Current State**: Index on PK.
- **Query Pattern**: Dashboard queries executions filtered by `agent_id` and `status`.
- **Recommendation**: Add index on `(agent_id, status)`.

---

## 2. N+1 Query Pattern Detection

### Organization Members Retrieval ([organizations.py](file:///d:/markai/apps/api/src/api/routes/organizations.py#L85-L105))
- **Issue**: Iterating `user_organizations` table to serialize member details causes a separate SQL `SELECT` for each associated `User` record if not eagerly loaded.
- **Remediation**: Use `options(joinedload(UserOrganization.user))` in SQLAlchemy query.

### RAG Chunk Document Enrichment ([rag_engine.py](file:///d:/markai/apps/api/src/api/services/rag_engine.py#L140-L160))
- **Issue**: Fetching matched chunks from vector results and subsequently fetching `KnowledgeDocument` titles line-by-line.
- **Remediation**: Execute bulk query with `selectinload(KnowledgeChunk.document)`.

---

## 3. Unused & Low Usage Tables

- **`conversation_bookmarks`** ([conversation_bookmark.py](file:///d:/markai/apps/api/src/api/models/conversation_bookmark.py)):
  - **Status**: **Unused / Partially Implemented**
  - **Details**: Model exists in ORM schema, but no active API routes in `routes/chat.py` perform write operations to this table.
- **`conversation_shares`** ([conversation_share.py](file:///d:/markai/apps/api/src/api/models/conversation_share.py)):
  - **Status**: **Unused / Potential Dead Code**
  - **Details**: Model exists, but share URL creation features are not exposed in frontend.
