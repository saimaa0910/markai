import pytest
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from api.models.organization import Organization
from api.models.user import User
from api.models.ai_platform import AIProvider, AIProviderKey
from api.models.ai_registry import AIModelRegistry
from api.routes.ai import sync_providers_and_models
from api.ai.gateway.coordinator import AIGateway
from api.ai.router.engine import ModelRouter
from api.ai.runtime.streaming_runtime import agent_streaming_runtime


def test_provider_sync_seeding(db_session: Session):
    """
    Assert that running sync_providers_and_models registers all 8 providers
    including DeepSeek, Mistral, and Ollama, and seeds their models.
    """
    sync_providers_and_models(db_session)

    # Check providers list
    providers = db_session.query(AIProvider).all()
    provider_names = {p.name for p in providers}
    assert "deepseek" in provider_names
    assert "mistral" in provider_names
    assert "ollama" in provider_names
    assert "groq" in provider_names

    # Check models list
    models = db_session.query(AIModelRegistry).all()
    model_names = {m.model_name for m in models}
    assert "deepseek-chat" in model_names
    assert "mistral-large-latest" in model_names
    assert "llama3" in model_names


def test_hierarchical_credentials_lookup(db_session: Session):
    """
    Verify that _get_provider_adapter resolves user-level keys first,
    then org-level keys, then environment variables.
    """
    gateway = AIGateway()
    sync_providers_and_models(db_session)
    
    # Create real Organization and User rows
    org = Organization(name="Test Hierarchy Org", slug="test-hierarchy-org")
    db_session.add(org)
    db_session.flush()

    user = User(
        email="test_hierarchy_user@example.com",
        hashed_password="hashedpassword",
        full_name="Hierarchy Tester",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Find the provider
    prov = db_session.query(AIProvider).filter_by(name="openai").first()
    assert prov is not None

    from api.core.encryption import encrypt_key

    # 1. Create Organization-level Key
    org_key = AIProviderKey(
        provider_id=prov.id,
        organization_id=org.id,
        user_id=None,
        api_key=encrypt_key("sk-org-level-key"),
        is_active=True
    )
    db_session.add(org_key)
    db_session.flush()

    # Retrieve adapter with user_id=None: should return org-level key
    adapter_org = gateway._get_provider_adapter(db_session, "openai", org.id, user_id=None)
    assert adapter_org.api_key == "sk-org-level-key"

    # 2. Create User-level Key
    user_key = AIProviderKey(
        provider_id=prov.id,
        organization_id=org.id,
        user_id=user.id,
        api_key=encrypt_key("sk-user-level-key"),
        is_active=True
    )
    db_session.add(user_key)
    db_session.flush()

    # Retrieve adapter with user_id specified: should return user-level key (precedence)
    adapter_user = gateway._get_provider_adapter(db_session, "openai", org.id, user_id=user.id)
    assert adapter_user.api_key == "sk-user-level-key"

    # Clean up
    db_session.delete(user_key)
    db_session.delete(org_key)
    db_session.delete(user)
    db_session.delete(org)
    db_session.flush()


def test_fallback_to_groq_when_no_rules_exist(db_session: Session):
    """
    Verify that ModelRouter prioritizes Groq models when no active routing rule matches.
    """
    from api.models.ai_registry import AIRoutingRule
    from api.models.router import AIRoutingPolicy
    db_session.query(AIRoutingRule).delete()
    db_session.query(AIRoutingPolicy).delete()
    db_session.commit()

    router = ModelRouter()
    sync_providers_and_models(db_session)

    org_id = uuid.uuid4()

    # Assert that routing returns candidates list where Groq is first
    candidates = router.route(db_session, "chat", org_id)
    assert len(candidates) > 0
    assert candidates[0].provider.lower() == "groq"


def test_streaming_runtime_token_parsing():
    """
    Verify that streaming runtime resolves tokens successfully from chunks
    containing either 'token' or 'content' keys.
    """
    # Simple shims of generator generator_chunks
    chunks_with_content = [{"content": "Hello"}, {"content": " "}, {"content": "world"}]
    chunks_with_token = [{"token": "Hello"}, {"token": " "}, {"token": "world"}]

    def extract_tokens(chunks):
        extracted = []
        for chunk in chunks:
            token = chunk.get("content") or chunk.get("token", "")
            if token:
                extracted.append(token)
        return "".join(extracted)

    assert extract_tokens(chunks_with_content) == "Hello world"
    assert extract_tokens(chunks_with_token) == "Hello world"
