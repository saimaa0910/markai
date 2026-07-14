import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from api.models.organization import Organization
from api.models.user import User
from api.models.prompt import Prompt
from api.models.conversation import Conversation
from api.models.message import Message
from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.models.ai_usage import AITokenUsage
from api.models.knowledge import KnowledgeDocument, DocumentChunk


def test_ai_gateway_db_schemas(db_session: Session):
    """
    Verify that AI Gateway 2.0 database tables, columns, and relations
    are fully functional and correctly configured.
    """
    # 1. Setup sample organization and user
    org = Organization(name="AI Corp", slug="ai-corp")
    db_session.add(org)
    db_session.commit()

    user = User(
        email="test_gateway@example.com",
        hashed_password="hashedpassword",
        full_name="Gateway Tester",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # 2. Test AIModelRegistry table insertion
    model = AIModelRegistry(
        provider="groq",
        model_name="llama-3-70b-preview",
        context_window=8192,
        supports_streaming=True,
        supports_vision=False,
        supports_json=True,
        supports_embeddings=False,
        input_token_price=Decimal("0.5900"),
        output_token_price=Decimal("0.7900"),
        latency=Decimal("0.25"),
        priority=1,
        is_healthy=True,
        organization_id=org.id,
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)

    assert model.id is not None
    assert model.model_name == "llama-3-70b-preview"
    assert float(model.input_token_price) == 0.5900

    # 3. Test AIRoutingRule table insertion
    rule = AIRoutingRule(
        request_type="chat",
        model_registry_id=model.id,
        is_active=True,
        organization_id=org.id,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    assert rule.id is not None
    assert rule.model.model_name == "llama-3-70b-preview"

    # 4. Test AITokenUsage table insertion
    usage = AITokenUsage(
        organization_id=org.id,
        user_id=user.id,
        provider="groq",
        model_name="llama-3-70b-preview",
        prompt_tokens=150,
        completion_tokens=250,
        total_tokens=400,
        cost_usd=Decimal("0.000320"),
        latency_ms=280,
        status="success",
    )
    db_session.add(usage)
    db_session.commit()
    db_session.refresh(usage)

    assert usage.id is not None
    assert usage.total_tokens == 400
    assert float(usage.cost_usd) == 0.000320

    # 5. Test KnowledgeDocument and DocumentChunk table insertions
    doc = KnowledgeDocument(
        title="Marketing Strategy.pdf",
        file_type="pdf",
        organization_id=org.id,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None

    chunk = DocumentChunk(
        document_id=doc.id,
        organization_id=org.id,
        content="This is the first segment of our strategy plan.",
        embedding=[0.01, 0.02, 0.03] + [0.0] * 1533,  # 1536 dims
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    assert chunk.id is not None
    assert chunk.document.title == "Marketing Strategy.pdf"
    assert len(chunk.embedding) == 1536
    assert chunk.embedding[0] == 0.01

    # 6. Verify modified columns in Prompt
    prompt = Prompt(
        name="Gateway Prompt",
        content="Summarize: {text}",
        category="summarization",
        tags="marketing,strategy",
        is_shared=True,
        organization_id=org.id,
    )
    db_session.add(prompt)
    db_session.commit()
    db_session.refresh(prompt)

    assert prompt.category == "summarization"
    assert prompt.tags == "marketing,strategy"
    assert prompt.is_shared is True

    # 7. Verify modified columns in Message
    conv = Conversation(
        title="Gateway Conversation",
        user_id=user.id,
        organization_id=org.id,
    )
    db_session.add(conv)
    db_session.commit()

    msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content="Response here",
        model_used="llama-3-70b-preview",
        provider_used="groq",
        latency_ms=180,
        prompt_tokens=10,
        completion_tokens=20,
        cost_usd=Decimal("0.000015"),
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)

    assert msg.provider_used == "groq"
    assert msg.latency_ms == 180
    assert float(msg.cost_usd) == 0.000015
