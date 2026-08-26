import pytest
import uuid
from sqlalchemy.orm import Session
from api.ai.router.engine import ModelRouter
from api.ai.registry.manager import ModelRegistryManager
from api.models.ai_registry import AIModelRegistry


def test_router_strategies_integration(db_session: Session):
    # Seed default models
    ModelRegistryManager.seed_default_models(db_session)
    router = ModelRouter()

    # 1. Test 'cheapest' strategy
    cheapest_candidates = router.route(
        db=db_session,
        request_type="chat",
        strategy="cheapest",
    )
    assert len(cheapest_candidates) > 0
    # First candidate should have lowest sum of input/output token price
    for i in range(len(cheapest_candidates) - 1):
        price_curr = cheapest_candidates[i].input_token_price + cheapest_candidates[i].output_token_price
        price_next = cheapest_candidates[i + 1].input_token_price + cheapest_candidates[i + 1].output_token_price
        assert price_curr <= price_next

    # 2. Test 'fastest' strategy
    fastest_candidates = router.route(
        db=db_session,
        request_type="chat",
        strategy="fastest",
    )
    assert len(fastest_candidates) > 0
    for i in range(len(fastest_candidates) - 1):
        assert fastest_candidates[i].latency <= fastest_candidates[i + 1].latency

    # 3. Test 'highest_quality' strategy
    quality_candidates = router.route(
        db=db_session,
        request_type="chat",
        strategy="highest_quality",
    )
    assert len(quality_candidates) > 0
    for i in range(len(quality_candidates) - 1):
        assert quality_candidates[i].priority >= quality_candidates[i + 1].priority

    # 4. Test 'vision' required feature filtering
    vision_candidates = router.route(
        db=db_session,
        request_type="vision",
        required_features=["vision"],
    )
    assert len(vision_candidates) > 0
    for c in vision_candidates:
        assert c.supports_vision is True
