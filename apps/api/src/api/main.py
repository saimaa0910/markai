from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.core.config import settings
from api.routes import (
    auth, users, organizations, crm, ai, generator, campaigns, files,
    agents, memory, workflows, integrations, notifications, analytics,
    infrastructure, router, security, observability, prompts
)
from api.routes.chat import chat_router
from api.routes.sessions import router as sessions_router
from api.routes.rbac import router as rbac_router
from api.routes.audit import router as audit_router
from api.middleware.logging import LoggingMiddleware
from api.middleware.telemetry_middleware import TelemetryMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set CORS origins cleanly for credentialed requests
dev_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
configured_origins = [o for o in settings.cors_origins_list if o != "*"]
allowed_origins = list(set(dev_origins + configured_origins))

app.add_middleware(LoggingMiddleware)
app.add_middleware(TelemetryMiddleware)
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
app.include_router(prompts.router, prefix=settings.API_V1_STR)
app.include_router(ai.prompts_router, prefix=settings.API_V1_STR)
app.include_router(ai.conversations_router, prefix=settings.API_V1_STR)
app.include_router(ai.knowledge_router, prefix=settings.API_V1_STR)
app.include_router(ai.models_router, prefix=settings.API_V1_STR)
app.include_router(ai.routing_rules_router, prefix=settings.API_V1_STR)
app.include_router(ai.usage_router, prefix=settings.API_V1_STR)
app.include_router(ai.providers_router, prefix=settings.API_V1_STR)
app.include_router(ai.playground_router, prefix=settings.API_V1_STR)
app.include_router(ai.compare_router, prefix=settings.API_V1_STR)
app.include_router(router.router, prefix=settings.API_V1_STR)
app.include_router(ai.analytics_router, prefix=settings.API_V1_STR)
app.include_router(generator.generator_router, prefix=settings.API_V1_STR)
app.include_router(campaigns.campaigns_router, prefix=settings.API_V1_STR)
app.include_router(files.router, prefix=settings.API_V1_STR)
app.include_router(agents.router, prefix=settings.API_V1_STR)
app.include_router(memory.router, prefix=settings.API_V1_STR)
app.include_router(workflows.router, prefix=settings.API_V1_STR)
app.include_router(integrations.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(infrastructure.router, prefix=settings.API_V1_STR)
app.include_router(security.router, prefix=settings.API_V1_STR)
app.include_router(observability.router, prefix=settings.API_V1_STR)
app.include_router(sessions_router, prefix=settings.API_V1_STR)
app.include_router(rbac_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def on_startup():
    from api.core.telemetry import init_telemetry
    init_telemetry(app)

    from api.services.email_service import validate_email_config
    validate_email_config()

    from api.database.session import SessionLocal
    from api.models.organization import Organization
    from api.models.user import User
    from api.models.membership import UserOrganization, UserRole
    from api.models.auth import Role, Permission
    from api.core.security import get_password_hash
    
    db = SessionLocal()
    try:
        # Seed permissions
        perms_to_seed = {
            "manage_users": "Manage organization members and roles",
            "manage_billing": "Manage billing subscription and details",
            "create_content": "Create prompts and campaign content",
            "view_analytics": "View dashboard analytics and reports",
        }
        db_perms = {}
        for perm_name, desc in perms_to_seed.items():
            perm = db.query(Permission).filter(Permission.name == perm_name).first()
            if not perm:
                perm = Permission(name=perm_name, description=desc)
                db.add(perm)
                db.flush()
            db_perms[perm_name] = perm
        
        # Seed roles and link permissions
        roles_to_seed = {
            "OWNER": (
                "Organization Owner with all permissions",
                ["manage_users", "manage_billing", "create_content", "view_analytics"],
            ),
            "ADMIN": (
                "Organization Administrator with management permissions",
                ["manage_users", "create_content", "view_analytics"],
            ),
            "MEMBER": (
                "Standard Organization Member",
                ["create_content", "view_analytics"],
            ),
            "GUEST": (
                "Read-only Guest User",
                ["view_analytics"],
            ),
        }
        for role_name, (desc, perm_names) in roles_to_seed.items():
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=desc)
                db.add(role)
                db.flush()
            
            # Update permissions
            role.permissions = [db_perms[pn] for pn in perm_names if pn in db_perms]
        
        db.commit()

        # Seed initial models & providers registry on every startup
        from api.routes.ai import sync_providers_and_models
        sync_providers_and_models(db)

        user_exists = db.query(User).first()
        if not user_exists:
            # Seed default admin user
            admin_user = User(
                email="admin@viptant.ai",
                hashed_password=get_password_hash("adminpassword"),
                full_name="Default Administrator",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            # Seed default organization
            org = Organization(
                name="Viptant Enterprise",
                slug="viptant-enterprise",
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            
            # Seed Owner membership
            membership = UserOrganization(
                user_id=admin_user.id,
                organization_id=org.id,
                role=UserRole.OWNER,
            )
            db.add(membership)
            db.commit()
            
            print("Successfully seeded initial tenant organization and admin user credentials.")
            
        # Initialize AgentRegistry and sync manifests to database
        try:
            from api.ai.agents.base.registry import AgentRegistry
            AgentRegistry.initialize()
            AgentRegistry.sync_to_db(db)
            print("Successfully synchronized AI Agent Registry manifests to the database.")
        except Exception as registry_err:
            print(f"Error initializing or syncing Agent Registry: {registry_err}")
            
        from api.tasks.account_cleanup import schedule_cleanup_job
        schedule_cleanup_job()
        print("Account cleanup scheduler started (daily at 02:00 UTC)")

    except Exception as e:
        print(f"Error seeding initial startup data: {e}")
    finally:
        db.close()




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
