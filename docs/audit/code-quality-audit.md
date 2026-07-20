# Code Quality & Complexity Audit

## Overview

This audit evaluates code maintainability, file sizing, function length, and architectural hygiene across both the `apps/api` (FastAPI backend) and `apps/web` (Next.js frontend) codebases.

---

## Code Quality Metrics Summary

- **Total Backend Python Files**: 100+ files
- **Total Frontend TypeScript/TSX Files**: 50+ files
- **Large Files (> 500 lines)**:
  - [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py) (~1,200 lines / 53 KB) — Primary AI Gateway Coordinator handling multi-provider routing, rate limiting, and fallback cascades.
  - [ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py) (~1,400 lines / 62 KB) — Core AI Platform Route Controller handling prompts, knowledge, usage analytics, models, and playground execution.
  - [knowledge.py](file:///d:/markai/apps/api/src/api/routes/knowledge.py) (~900 lines / 46 KB) — Knowledge base route controller handling chunking, vector uploads, and RAG execution.
  - [chat.py](file:///d:/markai/apps/api/src/api/routes/chat.py) (~800 lines / 38 KB) — Chat conversation and real-time streaming endpoint controller.

---

## Areas for Architectural Refactoring

### 1. Route Controller Splitting (`routes/ai.py` and `routes/knowledge.py`)
- **Current State**: `routes/ai.py` contains 10 distinct sub-routers (Prompts, Knowledge, Models, Routing Rules, Usage, Providers, Playground, Compare, Analytics).
- **Refactoring Recommendation**: Separate sub-routers into individual modules under a `routes/ai/` directory to improve maintainability.

### 2. Provider Mock Fallback Standardization
- **Current State**: Each provider (`openai.py`, `claude.py`, `gemini.py`, `groq.py`, `openrouter.py`) implements its own fallback stream simulation when provider API keys are missing or invalid.
- **Refactoring Recommendation**: Extract mock stream generation into a dedicated `MockLLMProvider` class in `ai/providers/mock.py`.

### 3. Frontend Dashboard Page Modularization (`dashboard/page.tsx`)
- **Current State**: The main overview page ([dashboard/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/page.tsx)) contains 12KB of inline React components and layout code.
- **Refactoring Recommendation**: Break KPI cards, charts, and activity feeds into standalone reusable components in `features/analytics/`.
