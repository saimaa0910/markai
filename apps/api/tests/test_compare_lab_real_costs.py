import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from api.ai.gateway.coordinator import AIGateway
from api.ai.registry.manager import ModelRegistryManager
from api.models.ai_registry import AIModelRegistry


def test_compare_lab_dynamic_cost_calculation(db_session: Session):
    ModelRegistryManager.seed_default_models(db_session)
    gateway = AIGateway()

    # Query diverse models
    gpt4o = db_session.query(AIModelRegistry).filter(AIModelRegistry.model_name == "gpt-4o-mini").first()
    llama = db_session.query(AIModelRegistry).filter(AIModelRegistry.model_name == "llama3-8b-8192").first()

    assert gpt4o is not None
    assert llama is not None

    # Calculate costs dynamically using prices from DB registry
    cost_gpt4o = gateway._calculate_cost(
        prompt_tokens=1000,
        completion_tokens=500,
        input_price=gpt4o.input_token_price,
        output_price=gpt4o.output_token_price,
    )

    cost_llama = gateway._calculate_cost(
        prompt_tokens=1000,
        completion_tokens=500,
        input_price=llama.input_token_price,
        output_price=llama.output_token_price,
    )

    assert float(cost_gpt4o) > 0.0
    assert float(cost_llama) >= 0.0
    assert float(cost_gpt4o) > float(cost_llama)
