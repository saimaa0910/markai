from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.core.config import settings
from api.routes import (
    auth, users, organizations, crm, ai, generator, campaigns, files,
    agents, memory, workflows, integrations, notifications, analytics
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set CORS origins
allowed_origins = ["*"] if settings.ENVIRONMENT == "development" else settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(organizations.router, prefix=settings.API_V1_STR)
app.include_router(crm.companies_router, prefix=settings.API_V1_STR)
app.include_router(crm.contacts_router, prefix=settings.API_V1_STR)
app.include_router(crm.leads_router, prefix=settings.API_V1_STR)
app.include_router(crm.activities_router, prefix=settings.API_V1_STR)
app.include_router(ai.prompts_router, prefix=settings.API_V1_STR)
app.include_router(ai.conversations_router, prefix=settings.API_V1_STR)
app.include_router(ai.knowledge_router, prefix=settings.API_V1_STR)
app.include_router(ai.models_router, prefix=settings.API_V1_STR)
app.include_router(ai.routing_rules_router, prefix=settings.API_V1_STR)
app.include_router(ai.usage_router, prefix=settings.API_V1_STR)
app.include_router(generator.generator_router, prefix=settings.API_V1_STR)
app.include_router(campaigns.campaigns_router, prefix=settings.API_V1_STR)
app.include_router(files.router, prefix=settings.API_V1_STR)
app.include_router(agents.router, prefix=settings.API_V1_STR)
app.include_router(memory.router, prefix=settings.API_V1_STR)
app.include_router(workflows.router, prefix=settings.API_V1_STR)
app.include_router(integrations.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler returning standardized error formatting.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "details": {"type": type(exc).__name__, "error": str(exc)},
            },
        },
    )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """
    Root level simple health check endpoint.
    """
    return {"success": True, "status": "healthy", "service": settings.PROJECT_NAME}


@app.get(f"{settings.API_V1_STR}/health", status_code=status.HTTP_200_OK)
async def api_health_check() -> dict[str, Any]:
    """
    API versioned health check endpoint.
    """
    return {"success": True, "status": "healthy", "version": "v1"}


@app.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict[str, Any]:
    """
    Liveness check for standard ping response.
    """
    return {"status": "alive", "success": True}


@app.get(f"{settings.API_V1_STR}/live")
async def api_liveness_check() -> Any:
    return await liveness_check()


@app.get("/ready")
async def readiness_check() -> Any:
    """
    Readiness check verifying DB, Redis, MinIO port, and AI Registry health state.
    """
    checks = {
        "database": False,
        "redis": False,
        "minio": False,
        "ai_gateway": False,
    }
    
    # 1. Database Connectivity Check
    try:
        from api.database.session import SessionLocal
        from sqlalchemy import text
        db_sess = SessionLocal()
        try:
            db_sess.execute(text("SELECT 1"))
            checks["database"] = True
        finally:
            db_sess.close()
    except Exception:
        pass

    # 2. Redis Connectivity Check
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        r.ping()
        checks["redis"] = True
    except Exception:
        pass

    # 3. MinIO Connectivity Check
    try:
        import socket
        endpoint = settings.MINIO_ENDPOINT
        host, port = (endpoint.split(":") + ["80"])[:2]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        try:
            s.connect((host, int(port)))
            checks["minio"] = True
        finally:
            s.close()
    except Exception:
        pass

    # 4. AI Gateway Connectivity Check
    try:
        from api.database.session import SessionLocal
        from api.models.ai_registry import AIModelRegistry
        db_sess = SessionLocal()
        try:
            model = db_sess.query(AIModelRegistry).filter_by(is_healthy=True).first()
            if model:
                checks["ai_gateway"] = True
        finally:
            db_sess.close()
    except Exception:
        pass

    overall_healthy = all(checks.values())
    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "success": overall_healthy,
            "status": "ready" if overall_healthy else "unready",
            "checks": checks,
        }
    )


@app.get(f"{settings.API_V1_STR}/ready")
async def api_readiness_check() -> Any:
    return await readiness_check()
