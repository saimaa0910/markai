# Visual Architecture & Sequence Diagrams

## 1. High-Level Platform Architecture

```mermaid
graph TD
    Client([Enterprise User / Web Browser]) -->|HTTPS / SSE| Nginx[Nginx Reverse Proxy]
    
    subgraph Containerized Application Cluster
        Nginx -->|Port 3000| Web[Next.js 15 Web Application]
        Nginx -->|Port 8000| API[FastAPI Application Server]
        
        API --> AuthMiddleware[Auth & RBAC Middleware]
        API --> AIGateway[AI Gateway 2.0 & Router]
        API --> AgentEngine[AI Agent Engine]
        API --> RAGEngine[Knowledge & RAG Engine]
        API --> WorkflowEngine[Workflow Automation Engine]
    end

    subgraph Data & Persistence Infrastructure
        API --> DB[(PostgreSQL Database)]
        API --> Redis[(Redis Cache / Celery Broker)]
        API --> MinIO[(MinIO Object Storage)]
    end

    subgraph Asynchronous Task Cluster
        Redis --> Worker[Celery Task Workers]
        Redis --> Beat[Celery Beat Scheduler]
        Worker --> DB
        Worker --> MinIO
    end

    subgraph Multi-Provider AI Cloud
        AIGateway --> OpenAI[OpenAI API]
        AIGateway --> Claude[Anthropic Claude API]
        AIGateway --> Gemini[Google Gemini API]
        AIGateway --> Groq[Groq Cloud API]
        AIGateway --> OpenRouter[OpenRouter Proxy API]
    end
```

---

## 2. Multi-Provider Streaming AI Completion Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Web Client
    participant API as FastAPI Router (/ai/stream)
    participant Sec as AISecurityPipeline
    participant Router as AIRouterEngine
    participant Coord as AIGatewayCoordinator
    participant Provider as AI Provider (OpenAI/Claude/etc)
    participant DB as PostgreSQL Database

    User->>API: POST /api/v1/ai/stream (Prompt, Model/Policy)
    API->>Sec: Scan Prompt (Injection, Toxicity, PII)
    Sec-->>API: Prompt Clean / Approved
    API->>Router: Resolve Target Model (Cost/Latency/Fallback)
    Router-->>API: Target Model Selected (e.g. gpt-4o)
    API->>Coord: Stream Completion (Target Model, Prompt)
    Coord->>Provider: Initiate SSE Stream Request
    loop Token Streaming
        Provider-->>Coord: Stream Event (Token Chunk)
        Coord-->>API: SSE Chunk Event
        API-->>User: HTTP SSE EventSource Frame
    end
    Coord->>DB: Log Usage Record (Tokens & Estimated Cost)
```

---

## 3. Knowledge Document Ingestion & RAG Query Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Enterprise Admin
    participant API as FastAPI (/ai/knowledge/upload)
    participant Celery as Celery Worker
    participant Parser as DocumentParser
    participant Vector as VectorStoreService
    participant DB as PostgreSQL Database

    User->>API: Upload File (PDF/DOCX)
    API->>DB: Create KnowledgeDocument (Status: PENDING)
    API->>Celery: Enqueue process_document_pipeline_task
    API-->>User: HTTP 202 Accepted (Document Uploaded)
    
    Celery->>Parser: Extract Plain Text from File
    Parser-->>Celery: Extracted Raw Text
    Celery->>Celery: Chunk Text (500 tokens, 100 overlap)
    Celery->>Vector: Generate Embeddings for Chunks
    Vector-->>Celery: Vector Arrays
    Celery->>DB: Insert KnowledgeChunk Records + Vectors
    Celery->>DB: Update KnowledgeDocument (Status: COMPLETED)
```
