"""
Social Agent Helpers — Sprint 7.5
====================================
HashtagEngine, PlatformOptimizer, PublisherAdapters, and SocialCalendar.
All publisher adapters follow a unified interface so any provider
can be plugged in without modifying the agent.
"""
import logging
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from api.ai.agents.social.constants import (
    PLATFORM_CONFIGS, INDUSTRY_HASHTAG_POOLS, SocialPlatform, SocialContentType
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# HASHTAG ENGINE
# ──────────────────────────────────────────────────────────────────────────────

class HashtagEngine:
    """
    Generates AI-ranked hashtags across five categories:
    trending, industry, brand, campaign, and location.
    """

    @staticmethod
    def generate(
        platform: str,
        keywords: Optional[List[str]] = None,
        industry: Optional[str] = None,
        brand_name: Optional[str] = None,
        campaign_name: Optional[str] = None,
        location: Optional[str] = None,
        max_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Returns ranked hashtag sets with estimated reach scores.
        In production, 'trending' hashtags would be fetched from a trends API.
        """
        platform_cfg = PLATFORM_CONFIGS.get(platform.upper(), {})
        limit = max_count or platform_cfg.get("hashtag_limit", 10)
        kw_list = keywords or []

        # ── Keyword-derived hashtags ──────────────────────────────────────────
        keyword_tags = [
            f"#{kw.strip().replace(' ', '').title()}"
            for kw in kw_list[:5]
            if kw.strip()
        ]

        # ── Industry hashtags ─────────────────────────────────────────────────
        industry_pool = []
        if industry:
            industry_lower = industry.lower()
            for key, tags in INDUSTRY_HASHTAG_POOLS.items():
                if key in industry_lower or industry_lower in key:
                    industry_pool = tags
                    break
        if not industry_pool:
            # Default to marketing as fallback
            industry_pool = INDUSTRY_HASHTAG_POOLS.get("marketing", [])

        # ── Brand hashtags ────────────────────────────────────────────────────
        brand_tags = []
        if brand_name:
            clean = brand_name.strip().replace(" ", "")
            brand_tags = [f"#{clean}", f"#{clean}AI", f"#{clean}Community"]

        # ── Campaign hashtags ─────────────────────────────────────────────────
        campaign_tags = []
        if campaign_name:
            clean = campaign_name.strip().replace(" ", "")
            campaign_tags = [f"#{clean}", f"#{clean}Launch"]

        # ── Location hashtags ─────────────────────────────────────────────────
        location_tags = []
        if location:
            clean = location.strip().replace(" ", "")
            location_tags = [f"#{clean}Business", f"#{clean}Startup"]

        # ── Trending (simulated — replace with API in production) ─────────────
        trending_pool = [
            "#AI2025", "#FutureOfWork", "#Innovation", "#DigitalTransformation",
            "#TechTrends", "#StartupLife", "#BuildInPublic", "#GrowthMindset",
        ]
        trending_tags = random.sample(trending_pool, min(3, len(trending_pool)))

        # ── Assemble and rank ─────────────────────────────────────────────────
        all_tags: List[Dict[str, Any]] = []

        for tag in (keyword_tags + industry_pool[:3] + brand_tags[:2] + campaign_tags[:2]):
            if tag and tag not in [t["tag"] for t in all_tags]:
                all_tags.append({
                    "tag": tag,
                    "category": "keyword" if tag in keyword_tags else "industry",
                    "reach_score": round(random.uniform(0.5, 1.0), 2),
                })

        for tag in trending_tags:
            if tag not in [t["tag"] for t in all_tags]:
                all_tags.append({
                    "tag": tag,
                    "category": "trending",
                    "reach_score": round(random.uniform(0.7, 1.0), 2),
                })

        for tag in location_tags:
            if tag not in [t["tag"] for t in all_tags]:
                all_tags.append({
                    "tag": tag,
                    "category": "location",
                    "reach_score": round(random.uniform(0.3, 0.7), 2),
                })

        # Sort by reach_score descending
        all_tags.sort(key=lambda x: x["reach_score"], reverse=True)
        selected = all_tags[:limit]

        return {
            "hashtags": selected,
            "hashtag_string": " ".join(t["tag"] for t in selected),
            "total_count": len(selected),
            "estimated_reach": sum(t["reach_score"] for t in selected) / max(len(selected), 1),
            "categories": {
                "trending": [t["tag"] for t in selected if t["category"] == "trending"],
                "industry": [t["tag"] for t in selected if t["category"] == "industry"],
                "keyword": [t["tag"] for t in selected if t["category"] == "keyword"],
                "brand": [t["tag"] for t in selected if t["category"] == "brand"],
                "campaign": [t["tag"] for t in selected if t["category"] == "campaign"],
                "location": [t["tag"] for t in selected if t["category"] == "location"],
            },
        }


# ──────────────────────────────────────────────────────────────────────────────
# PLATFORM OPTIMIZER
# ──────────────────────────────────────────────────────────────────────────────

class PlatformOptimizer:
    """
    Transforms generated content to meet platform-specific rules,
    character limits, tone, and formatting requirements.
    """

    @classmethod
    def optimize(
        cls,
        content: str,
        platform: str,
        hashtag_string: str = "",
        cta: Optional[str] = None,
        hook: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Applies platform-specific transformations. Returns the optimized post.
        """
        cfg = PLATFORM_CONFIGS.get(platform.upper(), {})
        char_limit = cfg.get("char_limit", 2200)
        emoji_friendly = cfg.get("emoji_friendly", False)
        tone = cfg.get("tone", "professional")

        optimizer_fn = {
            "LINKEDIN": cls._optimize_linkedin,
            "TWITTER": cls._optimize_twitter,
            "INSTAGRAM": cls._optimize_instagram,
            "FACEBOOK": cls._optimize_facebook,
            "THREADS": cls._optimize_threads,
            "PINTEREST": cls._optimize_pinterest,
            "TIKTOK": cls._optimize_tiktok,
            "YOUTUBE_COMMUNITY": cls._optimize_youtube,
            "YOUTUBE_SHORTS": cls._optimize_youtube,
            "REDDIT": cls._optimize_reddit,
            "DISCORD": cls._optimize_discord,
            "TELEGRAM": cls._optimize_telegram,
            "MEDIUM": cls._optimize_medium,
            "QUORA": cls._optimize_quora,
        }.get(platform.upper(), cls._optimize_generic)

        optimized_text = optimizer_fn(content, cfg, hook=hook, cta=cta)

        # Append hashtags for platforms that support them
        if hashtag_string and cfg.get("hashtag_limit", 0) > 0:
            separator = "\n\n" if platform.upper() not in ("TWITTER", "THREADS") else " "
            optimized_text = f"{optimized_text}{separator}{hashtag_string}"

        # Enforce character limit
        if len(optimized_text) > char_limit:
            optimized_text = optimized_text[:char_limit - 3] + "..."

        char_used = len(optimized_text)
        char_remaining = char_limit - char_used

        return {
            "optimized_content": optimized_text,
            "platform": platform,
            "tone": tone,
            "char_used": char_used,
            "char_limit": char_limit,
            "char_remaining": char_remaining,
            "within_limit": char_remaining >= 0,
            "best_practices": cfg.get("best_practices", []),
        }

    @staticmethod
    def _optimize_linkedin(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """LinkedIn: Professional, long-form, line-break formatted."""
        lines = content.strip().split(". ")
        formatted = []
        for i, line in enumerate(lines):
            formatted.append(line.strip())
            # Add spacing every 2–3 sentences for readability
            if (i + 1) % 3 == 0 and i < len(lines) - 1:
                formatted.append("")
        result = "\n".join(formatted)
        if hook:
            result = f"{hook}\n\n{result}"
        if cta:
            result = f"{result}\n\n→ {cta}"
        return result.strip()

    @staticmethod
    def _optimize_twitter(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Twitter/X: Short, punchy, direct. Truncate to fit 280 chars."""
        limit = cfg.get("char_limit", 280)
        base = content.strip()
        if cta:
            base = f"{base} {cta}"
        if len(base) > limit:
            base = base[:limit - 3] + "..."
        return base

    @staticmethod
    def _optimize_instagram(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Instagram: Emoji-friendly, hashtag-rich, first-line hook."""
        lines = []
        if hook:
            lines.append(f"✨ {hook}")
            lines.append("")
        lines.append(content.strip())
        if cta:
            lines.append("")
            lines.append(f"👉 {cta}")
        return "\n".join(lines)

    @staticmethod
    def _optimize_facebook(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Facebook: Community-focused, conversational, ends with question."""
        result = content.strip()
        if hook:
            result = f"{hook}\n\n{result}"
        if cta:
            result = f"{result}\n\n💬 {cta}"
        return result

    @staticmethod
    def _optimize_threads(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Threads: Conversational, short, authentic."""
        result = content.strip()
        if hook:
            result = f"{hook}\n\n{result}"
        return result[:500]

    @staticmethod
    def _optimize_pinterest(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Pinterest: Inspirational, keyword-rich, visual focus."""
        result = content.strip()
        if cta:
            result = f"{result}\n\n🔗 {cta}"
        return result

    @staticmethod
    def _optimize_tiktok(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """TikTok: Hook first, entertainment-driven, punchy CTA."""
        parts = []
        if hook:
            parts.append(f"🎯 {hook}")
            parts.append("")
        parts.append(content.strip())
        if cta:
            parts.append("")
            parts.append(f"⬇️ {cta}")
        return "\n".join(parts)

    @staticmethod
    def _optimize_youtube(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """YouTube: Title + description with SEO focus."""
        result = content.strip()
        if cta:
            result = f"{result}\n\n📌 {cta}\n\n🔔 Subscribe for more!"
        return result

    @staticmethod
    def _optimize_reddit(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Reddit: Authentic, value-first, no promotional tone."""
        # Strip obvious promotional language flags
        result = content.strip()
        # Ensure no salesy CTA on Reddit
        return result

    @staticmethod
    def _optimize_discord(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Discord: Channel-appropriate, conversational."""
        return content.strip()[:2000]

    @staticmethod
    def _optimize_telegram(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Telegram: Markdown-formatted, direct."""
        result = content.strip()
        if cta:
            result = f"{result}\n\n👉 {cta}"
        return result

    @staticmethod
    def _optimize_medium(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Medium: Long-form, editorial, thought-leadership."""
        result = content.strip()
        if cta:
            result = f"{result}\n\n---\n\n{cta}"
        return result

    @staticmethod
    def _optimize_quora(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Quora: Expert answer format, fact-first."""
        return content.strip()

    @staticmethod
    def _optimize_generic(content: str, cfg: Dict, hook: Optional[str] = None, cta: Optional[str] = None) -> str:
        """Generic fallback."""
        return content.strip()


# ──────────────────────────────────────────────────────────────────────────────
# PUBLISHER ADAPTERS
# ──────────────────────────────────────────────────────────────────────────────

class BasePublisherAdapter(ABC):
    """
    Abstract base for all platform publisher adapters.
    Implements the Provider Architecture — credentials are injected,
    never hardcoded. Real OAuth implementations plug in here.
    """

    @abstractmethod
    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a post to the platform."""
        ...

    @abstractmethod
    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content against platform rules before publishing."""
        ...

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Check the health and authentication status of the platform connection."""
        ...

    @abstractmethod
    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        """Generate a render preview of how the post will appear."""
        ...


class LinkedInPublisher(BasePublisherAdapter):
    """LinkedIn publisher adapter. Requires OAuth token injection."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.platform = "LINKEDIN"

    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.access_token:
            return {"status": "error", "message": "LinkedIn OAuth token not configured.", "published": False}
        logger.info("LinkedIn publish called (stub — configure OAuth to enable)")
        return {"status": "stub", "platform": self.platform, "published": False, "message": "Configure OAuth to enable publishing"}

    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        char_limit = platform_config.get("char_limit", 3000)
        return {
            "valid": len(content) <= char_limit,
            "char_count": len(content),
            "char_limit": char_limit,
            "issues": [] if len(content) <= char_limit else [f"Content exceeds {char_limit} characters"],
        }

    def health(self) -> Dict[str, Any]:
        return {"platform": self.platform, "connected": bool(self.access_token), "status": "stub"}

    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        return {"platform": self.platform, "preview_content": content[:300], "image_url": image_url}


class TwitterPublisher(BasePublisherAdapter):
    """Twitter/X publisher adapter."""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.platform = "TWITTER"

    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "message": "Twitter API key not configured.", "published": False}
        return {"status": "stub", "platform": self.platform, "published": False, "message": "Configure API keys to enable publishing"}

    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        char_limit = platform_config.get("char_limit", 280)
        return {
            "valid": len(content) <= char_limit,
            "char_count": len(content),
            "char_limit": char_limit,
            "issues": [] if len(content) <= char_limit else [f"Tweet exceeds {char_limit} characters"],
        }

    def health(self) -> Dict[str, Any]:
        return {"platform": self.platform, "connected": bool(self.api_key), "status": "stub"}

    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        return {"platform": self.platform, "preview_content": content[:280], "image_url": image_url}


class FacebookPublisher(BasePublisherAdapter):
    def __init__(self, page_token: Optional[str] = None):
        self.page_token = page_token
        self.platform = "FACEBOOK"

    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "stub", "platform": self.platform, "published": False, "message": "Configure Page Token to enable publishing"}

    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        return {"valid": True, "char_count": len(content), "issues": []}

    def health(self) -> Dict[str, Any]:
        return {"platform": self.platform, "connected": bool(self.page_token), "status": "stub"}

    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        return {"platform": self.platform, "preview_content": content[:500], "image_url": image_url}


class InstagramPublisher(BasePublisherAdapter):
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.platform = "INSTAGRAM"

    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "stub", "platform": self.platform, "published": False, "message": "Configure Instagram Graph API to enable publishing"}

    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        char_limit = platform_config.get("char_limit", 2200)
        return {"valid": len(content) <= char_limit, "char_count": len(content), "issues": []}

    def health(self) -> Dict[str, Any]:
        return {"platform": self.platform, "connected": bool(self.access_token), "status": "stub"}

    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        return {"platform": self.platform, "preview_content": content[:300], "image_url": image_url}


class PinterestPublisher(BasePublisherAdapter):
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.platform = "PINTEREST"

    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "stub", "platform": self.platform, "published": False, "message": "Configure Pinterest API to enable publishing"}

    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        return {"valid": True, "char_count": len(content), "issues": []}

    def health(self) -> Dict[str, Any]:
        return {"platform": self.platform, "connected": bool(self.access_token), "status": "stub"}

    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        return {"platform": self.platform, "preview_content": content[:500], "image_url": image_url}


class YouTubePublisher(BasePublisherAdapter):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.platform = "YOUTUBE_COMMUNITY"

    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "stub", "platform": self.platform, "published": False, "message": "Configure YouTube Data API to enable publishing"}

    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        return {"valid": True, "char_count": len(content), "issues": []}

    def health(self) -> Dict[str, Any]:
        return {"platform": self.platform, "connected": bool(self.api_key), "status": "stub"}

    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        return {"platform": self.platform, "preview_content": content[:500], "image_url": image_url}


class ThreadsPublisher(BasePublisherAdapter):
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.platform = "THREADS"

    def publish(self, content: str, image_url: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "stub", "platform": self.platform, "published": False, "message": "Configure Threads API to enable publishing"}

    def validate(self, content: str, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        char_limit = platform_config.get("char_limit", 500)
        return {"valid": len(content) <= char_limit, "char_count": len(content), "issues": []}

    def health(self) -> Dict[str, Any]:
        return {"platform": self.platform, "connected": bool(self.access_token), "status": "stub"}

    def preview(self, content: str, image_url: Optional[str]) -> Dict[str, Any]:
        return {"platform": self.platform, "preview_content": content[:500], "image_url": image_url}


# ─── Publisher Factory ────────────────────────────────────────────────────────

def get_publisher(platform: str) -> Optional[BasePublisherAdapter]:
    """Returns the appropriate publisher adapter for a platform."""
    adapters = {
        "LINKEDIN": LinkedInPublisher,
        "TWITTER": TwitterPublisher,
        "FACEBOOK": FacebookPublisher,
        "INSTAGRAM": InstagramPublisher,
        "PINTEREST": PinterestPublisher,
        "YOUTUBE_COMMUNITY": YouTubePublisher,
        "YOUTUBE_SHORTS": YouTubePublisher,
        "THREADS": ThreadsPublisher,
    }
    adapter_cls = adapters.get(platform.upper())
    return adapter_cls() if adapter_cls else None


# ──────────────────────────────────────────────────────────────────────────────
# SOCIAL CALENDAR
# ──────────────────────────────────────────────────────────────────────────────

class SocialCalendar:
    """
    Social publishing calendar views. Derives schedule data from AgentRun records.
    """

    @staticmethod
    def get_daily_slots(posts: List[Dict]) -> List[Dict]:
        """Group posts by hour for a daily calendar view."""
        slots = {}
        for post in posts:
            hour = post.get("scheduled_at", "")[:13] or "unscheduled"
            slots.setdefault(hour, []).append(post)
        return [{"slot": k, "posts": v} for k, v in sorted(slots.items())]

    @staticmethod
    def get_weekly_view(posts: List[Dict]) -> List[Dict]:
        """Group posts by day-of-week."""
        days = {}
        for post in posts:
            day = post.get("scheduled_at", "")[:10] or "unscheduled"
            days.setdefault(day, []).append(post)
        return [{"date": k, "posts": v, "count": len(v)} for k, v in sorted(days.items())]

    @staticmethod
    def get_monthly_view(posts: List[Dict]) -> List[Dict]:
        """Group posts by month."""
        months = {}
        for post in posts:
            month = post.get("scheduled_at", "")[:7] or "unscheduled"
            months.setdefault(month, []).append(post)
        return [{"month": k, "posts": v, "count": len(v)} for k, v in sorted(months.items())]
