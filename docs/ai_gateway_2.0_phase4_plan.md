# AI Gateway 2.0: Phase 4 (RAG & Knowledge Indexing) - Implementation Plan

## Goal Description
Implement retrieval-augmented generation (RAG) and knowledge indexing features inside the Viptant modular monolith.

## Key Changes
1. **Models & Migrations**: Done in Phase 1 (`KnowledgeDocument`, `DocumentChunk`).
2. **Schemas**: Add schemas for uploading knowledge base documents and querying chunks.
3. **Knowledge Service**: Chunker engine, vector embeddings generator, SQLite cosine similarity math, and pgvector integrations.
4. **FastAPI Route Refactoring**: Implement API routes for Knowledge uploading/querying, and support RAG context injection inside convo message routing.

## Verification
Verify end-to-end functionality via automated integration tests (`tests/test_ai_gateway_phase4.py`).
