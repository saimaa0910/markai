"""
Social Agent Unit Tests — Sprint 7.5
======================================
Verifies core agent initialization, manifest definitions, registration,
validators, hashtag generation, platform optimizer, adapters, service flows,
and API routes.
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch

from api.models.agent import AgentType, AgentStatus, AgentSession, AgentRun
from api.ai.agents.base.registry import AgentRegistry
from api.ai.agents.social.manifest import SOCIAL_AGENT_MANIFEST
from api.ai.agents.social.agent import SocialAgent, social_agent
from api.ai.agents.social.helpers import HashtagEngine, PlatformOptimizer, get_publisher, SocialCalendar
from api.ai.agents.social.constants import PLATFORM_CONFIGS, SocialPlatform, SocialContentType, EngagementType
from api.ai.agents.social.validators import validate_social_input, validate_schedule_input, validate_publish_request
from api.ai.agents.social.service import SocialAgentService
from fastapi import HTTPException


class TestSocialAgentCore:
    """Verifies core initialization, manifests, and registry discovery."""

    def test_manifest_definitions(self):
        assert SOCIAL_AGENT_MANIFEST.id == "SOCIAL"
        assert "SOCIAL" in SOCIAL_AGENT_MANIFEST.capabilities
        assert "image_generation_tool" in SOCIAL_AGENT_MANIFEST.supported_tools
        assert "knowledge_tool" in SOCIAL_AGENT_MANIFEST.supported_tools

    def test_registry_registration(self):
        AgentRegistry.initialize()
        agent = AgentRegistry.get("SOCIAL")
        assert agent is not None
        assert isinstance(agent, SocialAgent)
        assert agent.manifest.id == "SOCIAL"


class TestSocialValidators:
    """Verifies social input parameter and platform limit validation rules."""

    def test_validate_social_input(self):
        # Valid input
        validate_social_input("Write a post about new SaaS", SocialPlatform.LINKEDIN, ["saas", "tech"])

        # Too short prompt
        with pytest.raises(HTTPException) as exc:
            validate_social_input("Short", SocialPlatform.LINKEDIN)
        assert exc.value.status_code == 400

        # Empty prompt
        with pytest.raises(HTTPException) as exc:
            validate_social_input("", SocialPlatform.LINKEDIN)
        assert exc.value.status_code == 400

        # Invalid keyword length
        with pytest.raises(HTTPException) as exc:
            validate_social_input("A valid social post prompt of 10+ characters", SocialPlatform.LINKEDIN, ["a" * 105])
        assert exc.value.status_code == 400

    def test_validate_schedule_input(self):
        import datetime
        # Valid schedule
        validate_schedule_input(
            scheduled_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
            timezone="UTC",
            recurring_pattern="every_monday_9am"
        )

        # Past schedule date
        with pytest.raises(HTTPException) as exc:
            validate_schedule_input(
                scheduled_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
            )
        assert exc.value.status_code == 400

        # Invalid recurring pattern
        with pytest.raises(HTTPException) as exc:
            validate_schedule_input(
                recurring_pattern="invalid_pattern"
            )
        assert exc.value.status_code == 400

    def test_validate_publish_request(self):
        # Valid publish request
        validate_publish_request("LINKEDIN", "A professional content caption")

        # Empty publish content
        with pytest.raises(HTTPException) as exc:
            validate_publish_request("LINKEDIN", "")
        assert exc.value.status_code == 400

        # Platform image support check
        with pytest.raises(HTTPException) as exc:
            validate_publish_request("TIKTOK", "caption text", "http://example.com/img.png")
        assert exc.value.status_code == 422


class TestHashtagEngine:
    """Verifies Hashtag Engine ranking and estimated reach scores."""

    def test_hashtag_generation(self):
        result = HashtagEngine.generate(
            platform="INSTAGRAM",
            keywords=["growth", "saas"],
            industry="marketing",
            brand_name="Viptant",
            campaign_name="Launch V2",
            max_count=10
        )

        assert "hashtags" in result
        assert "hashtag_string" in result
        assert result["total_count"] > 0
        assert len(result["hashtags"]) <= 10  # Default limit
        assert any(h["tag"] == "#Viptant" for h in result["hashtags"])
        assert any(h["category"] == "trending" for h in result["hashtags"])


class TestPlatformOptimizer:
    """Verifies tone, character counts, and best practice rules per platform."""

    def test_linkedin_optimization(self):
        content = "This is a social update. We are launching. Come check us out."
        res = PlatformOptimizer.optimize(
            content=content,
            platform="LINKEDIN",
            hashtag_string="#launch #tech",
            cta="Link in bio"
        )
        assert "optimized_content" in res
        assert "→ Link in bio" in res["optimized_content"]
        assert "#launch #tech" in res["optimized_content"]
        assert res["char_used"] > 0
        assert res["char_remaining"] > 0

    def test_twitter_optimization(self):
        content = "This is a twitter post that is supposed to be short and punchy."
        res = PlatformOptimizer.optimize(
            content=content,
            platform="TWITTER",
            hashtag_string="#news",
        )
        assert len(res["optimized_content"]) <= 280
        assert "#news" in res["optimized_content"]


class TestPublisherAdapters:
    """Verifies oauth and api credential injection interfaces."""

    def test_linkedin_publisher_stub(self):
        publisher = get_publisher("LINKEDIN")
        assert publisher is not None
        assert publisher.platform == "LINKEDIN"

        # Validate
        val = publisher.validate("Content", PLATFORM_CONFIGS["LINKEDIN"])
        assert val["valid"] is True

        # Preview
        prev = publisher.preview("Post copy", "http://image.url")
        assert prev["platform"] == "LINKEDIN"
        assert prev["preview_content"] == "Post copy"
        assert prev["image_url"] == "http://image.url"

        # Publish stub
        res = publisher.publish("Post content", None, {})
        assert res["published"] is False
        assert "OAuth" in res["message"]


class TestSocialCalendar:
    """Verifies daily slots, weekly views, and monthly views grouping."""

    def test_calendar_grouping(self):
        posts = [
            {"run_id": "1", "platform": "LINKEDIN", "scheduled_at": "2026-08-10T09:00:00Z"},
            {"run_id": "2", "platform": "TWITTER", "scheduled_at": "2026-08-10T14:30:00Z"},
            {"run_id": "3", "platform": "INSTAGRAM", "scheduled_at": "2026-08-11T10:00:00Z"},
        ]

        weekly = SocialCalendar.get_weekly_view(posts)
        assert len(weekly) == 2
        assert weekly[0]["count"] == 2
        assert weekly[1]["count"] == 1


class TestSocialAgentService:
    """Verifies database persistence logic and agent workflow coordination."""

    @patch("api.ai.agents.content.agent.ContentAgent.execute_generation")
    @patch("api.ai.agents.image.executor.ImageExecutor.generate")
    def test_generate_social_sync(self, mock_img_gen, mock_content_gen):
        mock_content_gen.return_value = {
            "generated_content": "A beautiful social update post.",
            "total_tokens": 120,
            "latency_ms": 300,
            "cost_usd": 0.0002,
        }
        mock_img_gen.return_value = {
            "storage_url": "http://minio/bucket/image.png",
        }

        db = MagicMock()
        session = MagicMock()
        session.id = uuid.uuid4()
        session.organization_id = uuid.uuid4()
        session.user_id = uuid.uuid4()
        session.agent.memory_enabled = False

        result = SocialAgentService.generate_social(
            db=db,
            session=session,
            platform=SocialPlatform.LINKEDIN,
            content_type=SocialContentType.POST,
            prompt="Write about our product launch",
            keywords=["launch", "saas"],
            generate_image=True,
            run_reflection=True,
            run_evaluation=True
        )

        assert result["platform"] == "LINKEDIN"
        assert result["content_type"] == "POST"
        assert result["image_url"] == "http://minio/bucket/image.png"
        assert result["content"]["headline"] == "A beautiful social update post."
        assert "evaluation" in result
        assert "reflection" in result
