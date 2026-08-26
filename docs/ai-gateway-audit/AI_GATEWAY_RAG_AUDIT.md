# EAIMOS AI GATEWAY — RAG & VECTOR SEARCH AUDIT

**Target:** `apps/api/src/api/services/vector_store.py` (`VectorStore`), `apps/api/src/api/services/rag_engine.py` (`RAGEngineService`), `apps/api/src/api/services/knowledge_service.py` (`KnowledgeService`), `apps/api/src/api/models/knowledge.py`.

---

## 1. RAG Architecture Overview

The EAIMOS Retrieval-Augmented Generation subsystem implements an enterprise document ingestion, semantic indexing, and multi-stage retrieval pipeline:

```
[User Document] ──► [Character Chunker] ──► [AIGateway.embeddings()] ──► [pgvector Upsert]
                                                                                │
                                                                                ▼
[Query Text] ──► [AIGateway.embeddings()]                                [DocumentChunk &
          │                                                              DocumentChunkEmbedding]
          ▼                                                                     │
┌───────────────────────────────┐                                              │
│        Hybrid Search          │ ◄────────────────────────────────────────────┘
│  pgvector Cosine (Dense) +    │
│  PostgreSQL FTS (Sparse Lex)  │
└──────────────┬────────────────┘
               │ RRF Ranking (k=60)
               ▼
┌───────────────────────────────┐
│     MMR Diversification       │ (lambda = 0.6)
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│   Cross-Encoder Re-ranking    │ (Heuristic / LLM Rescoring)
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Dynamic Context Builder &     │ Token Budget Window (12,000 Chars / ~3,000 Tokens)
│ Citation Tagging ([Source X]) │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│   AIGateway.chat() Inference  │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Hallucination Risk Evaluator  │ Keyword Overlap Density & Low-Confidence Fallback (<0.35)
└───────────────────────────────┘
```

---

## 2. Subsystem Audit Details

### 2.1 Database & Vector Indexing (`apps/api/src/api/models/knowledge.py`)
- **pgvector Integration**: `SafeVector(1536)` encapsulates `pgvector.sqlalchemy.Vector`.
- **Database Schema**:
  - `knowledge_documents`: Metadata, organization ID, status, progress, folder ID, collection ID.
  - `document_chunks`: Content, SHA256 content hash, token count, page number, chunk index.
  - `document_chunk_embeddings`: 1536-dimensional vector embedding column mapped to chunk ID.
- **Status**: `✅ COMPLETE`

### 2.2 Ingestion & Embedding Pipeline (`apps/api/src/api/services/knowledge_service.py`)
- **Chunking Algorithm**: Sliding window with character slicing (`chunk_size=500`, `overlap=100`).
- **Embedding Generation**: Calls `AIGateway.embeddings()` which delegates to `OpenAIProvider.embeddings()` (`text-embedding-3-small`).
- **Status**: `✅ COMPLETE` (Functional; note that character-based chunking lacks semantic boundary detection like markdown headers or sentence splitters).

### 2.3 Retrieval & Ranking (`apps/api/src/api/services/vector_store.py`)
- **Semantic Search**: Native SQL query ordering by `cosine_distance(query_embedding)`.
- **Keyword / Lexical Search**: PostgreSQL Full-Text Search (`to_tsvector('english', ...) @@ to_tsquery(...)`).
- **Hybrid Search**: Reciprocal Rank Fusion (RRF) with constant `k=60`:
  $$\text{Score}(d) = \frac{1}{60 + \text{rank}_{\text{semantic}}} + \frac{1}{60 + \text{rank}_{\text{keyword}}}$$
- **MMR Re-ranking**: Maximal Marginal Relevance with `lambda=0.6` to balance relevance and novelty.
- **Cross-Encoder Re-scoring**: Heuristic term boosting in development; structured LLM JSON scoring in production.
- **Status**: `✅ COMPLETE`

### 2.4 End-to-End Orchestrator (`apps/api/src/api/services/rag_engine.py`)
- **Context Construction**: Formats retrieved chunks as numbered sources (`[Source 1]`, `[Source 2]`) with token budget truncation (12,000 chars max).
- **Citation Resolution**: Regex extraction (`\[Source (\d+)\]`) maps cited sources to document records.
- **Hallucination Reducer**: If maximum retrieval similarity is below `0.35`, the engine returns a fallback response: *"I couldn't find supporting information in your knowledge base."*
- **Audit Logging**: Inserts search telemetry and latency into `KnowledgeSearchHistory`.
- **Status**: `✅ COMPLETE`

---

## 3. Dead Code & Stub Analysis

During audit, the following disconnected stub files were discovered:
1. `apps/api/src/api/ai/embeddings/embedder.py`:
   - Contains `EmbeddingService` with `return [0.0] * 1536`.
   - **Audit Verdict**: `🟠 MOCKED/SIMULATED` (Unused dead code; production calls `KnowledgeService` and `AIGateway.embeddings()`).
2. `apps/api/src/api/ai/rag/pipeline.py`:
   - Contains `RAGPipeline` returning dummy dicts.
   - **Audit Verdict**: `🟠 MOCKED/SIMULATED` (Unused dead code; production calls `RAGEngineService`).

---

## 4. Key Recommendations
1. Clean up unused stub files (`embedder.py` and `rag/pipeline.py`) to prevent developer confusion.
2. Upgrade character-based chunking in `KnowledgeService` to token-aware recursive semantic chunking.
3. Add HNSW indexing to `document_chunk_embeddings` for sub-10ms vector lookups at 1,000,000+ chunks scale.
