# Enterprise Services Layer

This directory contains standalone microservices and service orchestrators for the EAIMOS platform.

## Architecture Guidelines
- Each service must maintain its own domain boundaries.
- Define service interfaces in `@eaimos/types`.
- Implement robust telemetry and health-check endpoints.
