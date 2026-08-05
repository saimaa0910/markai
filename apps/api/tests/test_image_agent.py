import uuid
import pytest
from unittest.mock import MagicMock, patch

from api.models.agent import AgentType
from api.ai.agents.base.registry import AgentRegistry
from api.ai.agents.image.manifest import IMAGE_AGENT_MANIFEST
from api.ai.agents.image.agent import ImageAgent
from api.ai.agents.image.validators import validate_aspect_ratio, validate_style, validate_image_generation_request
from api.ai.agents.image.prompts import ImagePromptEngine
from api.ai.agents.image.prompt_optimizer import PromptOptimizer
from api.ai.agents.image.provider_router import ImageProviderRouter
from api.ai.agents.image.asset_manager import AssetManager
from api.ai.agents.image.reflection import image_reflector, ImageReflectionResult, ImageReflectionScores
from api.ai.agents.image.evaluation import image_evaluator
from api.ai.agents.image.constants import ASPECT_RATIOS, STYLE_LIBRARY
from api.ai.providers.base_provider import BaseProvider, ProviderRegistry
from api.ai.tools.registry import ToolRegistry
from fastapi import HTTPException


class TestImageAgentCore:
    """Verifies core initialization, manifests, and registry discovery."""

    def test_manifest_definitions(self):
        assert IMAGE_AGENT_MANIFEST.id == "IMAGE"
        assert "IMAGE" in IMAGE_AGENT_MANIFEST.capabilities
        assert "image_generate_tool" in IMAGE_AGENT_MANIFEST.supported_tools

    def test_registry_registration(self):
        AgentRegistry.initialize()
        agent = AgentRegistry.get("IMAGE")
        assert agent is not None
        assert isinstance(agent, ImageAgent)
        assert agent.manifest.id == "IMAGE"


class TestImageValidators:
    """Verifies layout sizes and style preset validation rules."""

    def test_validate_aspect_ratio(self):
        assert validate_aspect_ratio("16:9") is True
        assert validate_aspect_ratio("invalid_ratio") is False

    def test_validate_style(self):
        assert validate_style("apple") is True
        assert validate_style("invalid_style") is False

    def test_request_validation(self):
        # Valid request
        payload = {"prompt": "A modern laptop", "aspect_ratio": "16:9", "style": "minimal"}
        # Should not raise exception
        validate_image_generation_request(payload)

        # Invalid prompt
        with pytest.raises(HTTPException):
            validate_image_generation_request({"prompt": ""})

        # Invalid style
        with pytest.raises(HTTPException):
            validate_image_generation_request({"prompt": "A computer", "style": "cyber"})


class TestImagePromptEngine:
    """Verifies Prompt Engine compiles color palettes and style cues correctly."""

    def test_compile_prompt(self):
        prompt = "A sleek smartwatch placement"
        brand_ctx = {"brand_voice": "Bold, dynamic", "color_palette": "violet and fuchsia"}

        compiled = ImagePromptEngine.compile_prompt(
            user_prompt=prompt,
            style="apple",
            brand_context=brand_ctx
        )

        assert prompt in compiled
        assert "violet and fuchsia" in compiled
        assert STYLE_LIBRARY["apple"] in compiled


class TestProviderFramework:
    """Verifies the reusable BaseProvider and ProviderRegistry framework."""

    def test_registry_registration_and_retrieval(self):
        class MockCustomProvider(BaseProvider):
            @property
            def name(self) -> str:
                return "mock_custom"
            def capabilities(self):
                return {"supports_generation": True}
            def health(self):
                return True

        ProviderRegistry.register("mock_custom", MockCustomProvider)
        instance = ProviderRegistry.get_provider("mock_custom")
        assert instance is not None
        assert instance.name == "mock_custom"
        assert instance.capabilities()["supports_generation"] is True


class TestPromptOptimizer:
    """Verifies the multi-stage prompt optimization pipeline."""

    def test_optimize_prompt_pipeline(self):
        optimized = PromptOptimizer.optimize_prompt(
            user_prompt="A commercial layout mockup",
            template="landing_page_hero",
            lighting="soft studio",
            mood="optimistic",
            typography="Helvetica bold style",
            color_palette="pastel tones",
            brand_context={"brand_voice": "cozy corporate", "color_palette": "green and mint"},
            seo_keywords="best dashboard, SaaS design"
        )

        assert "commercial layout mockup" in optimized
        assert "landing page hero" in optimized.lower()
        assert "soft studio" in optimized
        assert "optimistic" in optimized
        assert "Helvetica bold style" in optimized
        assert "pastel tones" in optimized
        assert "cozy corporate" in optimized
        assert "best dashboard" in optimized


class TestSmartRouterFailover:
    """Verifies capabilities filtering and router automatic failover sequential loops."""

    @patch("requests.post")
    def test_failover_routing(self, mock_post):
        # Mocking database objects
        db = MagicMock()
        db_prov_1 = MagicMock()
        db_prov_1.id = uuid.uuid4()
        db_prov_1.name = "together"
        
        db_prov_2 = MagicMock()
        db_prov_2.id = uuid.uuid4()
        db_prov_2.name = "openai"

        # Mock query sequence returning first together, then openai
        db.scalars().first.side_effect = [db_prov_1, None, db_prov_2, None]

        router = ImageProviderRouter(db, uuid.uuid4())
        
        # Patch keys return to succeed
        with patch.object(router, "_get_key", return_value="fake_api_key"):
            # Mock get_provider to return together and openai
            prov_together = MagicMock()
            prov_together.name = "together"
            prov_together.capabilities.return_value = {"supports_generation": True}
            prov_together.generate.side_effect = RuntimeError("Service Unavailable")

            prov_openai = MagicMock()
            prov_openai.name = "openai"
            prov_openai.capabilities.return_value = {"supports_generation": True}
            prov_openai.generate.return_value = b"dalle_image_bytes"

            with patch("api.ai.providers.base_provider.ProviderRegistry.get_provider") as mock_get_provider:
                mock_get_provider.side_effect = lambda name: prov_together if name == "together" else prov_openai

                img_bytes, provider, model = router.generate_image(
                    prompt="High contrast landscape",
                    priority_override=["together", "openai"]
                )

                assert img_bytes == b"dalle_image_bytes"
                assert provider == "openai"
                assert prov_together.generate.called


class TestToolRegistryAlias:
    """Verifies that both tool names map back to the same generation implementation."""

    def test_alias_mapping(self):
        tool1 = ToolRegistry.get_tool("image_generate_tool")
        tool2 = ToolRegistry.get_tool("image_generation_tool")
        assert tool1 is not None
        assert tool2 is not None
        assert tool1 is tool2  # verify same singleton instance reference
