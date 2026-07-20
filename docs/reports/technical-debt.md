# Technical Debt & Improvement Opportunities

## Overview

This document explicitly catalogs technical debt, incomplete integrations, mock fallbacks, and temporary workarounds currently existing in the `markai` codebase.

---

## Technical Debt Inventory

### 1. Incomplete & Mocked Third-Party Integrations
- **Affected File**: [integration_service.py](file:///d:/markai/apps/api/src/api/services/integration_service.py)
- **Status**: **Partially Implemented**
- **Description**: Third-party integration connectors for Slack, HubSpot, and Salesforce currently use simulated OAuth authorization links and mock data syncing. Real OAuth handshake code and token refresh flows need to be plugged in when external app credentials are provided.

### 2. Provider Missing-Key Simulation Fallbacks
- **Affected Files**: [openai.py](file:///d:/markai/apps/api/src/api/ai/providers/openai.py), [claude.py](file:///d:/markai/apps/api/src/api/ai/providers/claude.py), [gemini.py](file:///d:/markai/apps/api/src/api/ai/providers/gemini.py), [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py), [openrouter.py](file:///d:/markai/apps/api/src/api/ai/providers/openrouter.py)
- **Status**: **Dev Fallback Active**
- **Description**: When `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or `GROQ_API_KEY` environment variables are empty, the providers fall back to simulated token stream generation.

### 3. OCR Document Parser Fallback
- **Affected File**: [document_parser.py](file:///d:/markai/apps/api/src/api/services/document_parser.py)
- **Status**: **Partially Implemented**
- **Description**: Scanned image PDF parsing falls back to mock string responses in non-production environments if Tesseract OCR or Vision LLMs are unconfigured.

### 4. Vector Store Embedding Generation
- **Affected File**: [vector_store.py](file:///d:/markai/apps/api/src/api/services/vector_store.py)
- **Status**: **In-Memory Fallback**
- **Description**: If FAISS or `pgvector` dependencies/drivers are not present, vector similarity search falls back to in-memory cosine similarity over local Python list structures.

### 5. Chat Bookmarks & Conversation Sharing
- **Affected Files**: [conversation_bookmark.py](file:///d:/markai/apps/api/src/api/models/conversation_bookmark.py), [conversation_share.py](file:///d:/markai/apps/api/src/api/models/conversation_share.py)
- **Status**: **Unused / Potential Dead Code**
- **Description**: Database models exist for conversation bookmarks and public share links, but corresponding API endpoints and frontend controls are not fully wired.
