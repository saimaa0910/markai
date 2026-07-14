from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.core.config import settings
from api.routes import auth, users, organizations, crm, ai, generator, campaigns, files

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
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
