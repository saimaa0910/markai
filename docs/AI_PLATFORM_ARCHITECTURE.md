# Enterprise AI Platform: Observability Architecture

This document details the high-level architecture, trace propagation, and metrics collection flows for Viptant's observability suite.

## High-Level Telemetry Flow

The diagram below maps the path of a gateway request, showing how telemetry contexts propagate to structured databases, Prometheus registries, and active incident workflows:

```mermaid
graph TD
    Client[HTTP Client] -->|Request with Headers| API_Ingress[FastAPI Routing & Ingress]
    
    subgraph API Middlewares [Middleware Pipelines]
        API_Ingress --> LM[LoggingMiddleware: Injects correlation / request IDs]
        LM --> TM[TelemetryMiddleware: Starts metrics timer]
    end
    
    subgraph Execution Layer [Gateway Core Engine]
        TM --> Coordinator[AIGateway Coordinator]
        Coordinator --> Security_In[AI Security Pipeline: Input validation]
        Security_In --> Router[Model Router: Healthy candidate selection]
        Router --> Adapt[Provider Adapters: LLM API Handshake]
        Adapt --> Security_Out[AI Security Pipeline: Output checks]
    end
    
    subgraph Observability Dispatchers [Telemetry Core Engines]
        Security_Out --> Logging[structlog: mask credentials & print JSON]
        Security_Out --> DB_Logs[Insert execution details into ai_logs table]
        Security_Out --> DB_Traces[Insert waterfall details into ai_traces table]
        Security_Out --> Prom[Increment Metrics counters & histograms]
        
        Adapt -->|Error / Timeout| Alert_Engine[Alert Engine / Incidents Tracker]
    end
    
    subgraph Data Stores & Exporters [System Backends]
        DB_Logs --> DB[(PostgreSQL / SQLite)]
        DB_Traces --> DB
        Alert_Engine --> DB
        
        Prom --> Scrape[/metrics scraped by Prometheus/]
        Scrape --> Grafana[Grafana Dashboards]
        
        Alert_Engine --> Slack[Slack webhook channel]
        Alert_Engine --> Email[Alert recipient email box]
    end
    
    subgraph Frontend Control [Web Dashboard]
        Admin[Next.js Observability Center] -->|Query REST APIs| API_Endpoints[Observability Routers]
        API_Endpoints --> DB
    end
```

## Trace Propagation Details

Trace IDs are passed along all systems:
1. **HTTP Layer**: Headers `x-correlation-id`, `x-request-id`, and `x-trace-id` track request scopes.
2. **Context Propagation**: Standard context variables (`contextvars`) propagate trace boundaries inside async tasks, ensuring SQLite and Postgres database records are linked back to the originating user request.
3. **Task Queues**: Celery task headers propagate correlation identifiers, linking asynchronous offline tasks to active user trace trees.
4. **Third-Party Providers**: Latencies, token quantities, and response codes are logged under the provider adapter sub-spans.
