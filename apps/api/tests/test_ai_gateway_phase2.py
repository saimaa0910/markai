import pytest
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from api.models.organization import Organization
from api.models.user import User
from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.models.ai_usage import AITokenUsage
from api.ai.registry.manager import ModelRegistryManager
from api.ai.router.engine import ModelRouter
from api.ai.gateway.coordinator import AIGateway


def test_ai_gateway_phase2_flow(db_session: Session):
    """
    Verify Model Registry seeding, Router matching, and Gateway fallback functionality.
    """
    # 1. Setup sample organization and user
    org = Organization(name="Phase 2 Corp", slug="phase-2-corp")
    db_session.add(org)
    db_session.commit()

    user = User(
        email="phase2_user@example.com",
        hashed_password="hashedpassword",
        full_name="Gateway Phase 2 Tester",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # 2. Seed Default Models
    ModelRegistryManager.seed_default_models(db_session)

    # Assert models were seeded
    models = db_session.query(AIModelRegistry).all()
    assert len(models) >= 6

    # 3. Test Routing Rules Resolving
    router = ModelRouter()
    
    # Route for 'chat'
    chat_candidates = router.route(db_session, "chat", org.id)
    assert len(chat_candidates) > 0
    assert chat_candidates[0].model_name == "llama3-70b-8192"

    # Route for 'vision'
    vision_candidates = router.route(db_session, "vision", org.id)
    assert len(vision_candidates) > 0
    assert vision_candidates[0].model_name == "gemini-1.5-flash"

    # 4. Test Gateway Executions & Cost Calculations
    gateway = AIGateway()
    messages = [{"role": "user", "content": "Hello!"}]
    
    res = gateway.chat(
        db=db_session,
        messages=messages,
        organization_id=org.id,
        user_id=user.id,
        temperature=0.7,
    )

    assert "content" in res
    assert "[Simulated" in res["content"]

    # Check that success log is in DB
    logs = db_session.query(AITokenUsage).filter_by(status="success", organization_id=org.id).all()
    assert len(logs) == 1
    assert logs[0].model_name == "llama3-70b-8192"
    assert logs[0].total_tokens > 0

    # 5. Test Fallback Routing
    # Force primary model (llama3-70b-8192 on Groq) to fail by patching its provider's chat function
    groq_provider = gateway.providers["groq"]
    original_chat = groq_provider.chat

    def failing_chat(*args, **kwargs):
        raise RuntimeError("Groq API rate limit exceeded")

    groq_provider.chat = failing_chat

    # Call chat again: it should fallback to the next chat model in priority
    fallback_res = gateway.chat(
        db=db_session,
        messages=messages,
        organization_id=org.id,
        user_id=user.id,
    )

    # Assert fallback succeeded (it used another provider/model in the registry list)
    assert "content" in fallback_res
    
    # Check that llama3-70b-8192 was marked unhealthy (is_healthy == False)
    unhealthy_model = db_session.query(AIModelRegistry).filter_by(model_name="llama3-70b-8192").first()
    assert unhealthy_model.is_healthy is False

    # Check failure and subsequent success logs in DB
    failure_log = db_session.query(AITokenUsage).filter_by(status="failure", organization_id=org.id).first()
    assert failure_log is not None
    assert failure_log.model_name == "llama3-70b-8192"
    assert "rate limit" in failure_log.error_message

    # Restore
    groq_provider.chat = original_chat
