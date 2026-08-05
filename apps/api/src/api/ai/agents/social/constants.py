"""
Social Agent Constants — Sprint 7.5
=====================================
Platform configurations, content types, limits, SSE events, and publisher registry.
"""
import enum
from typing import Dict, Any, List


# ─── Platform Enum ────────────────────────────────────────────────────────────

class SocialPlatform(str, enum.Enum):
    LINKEDIN = "LINKEDIN"
    TWITTER = "TWITTER"
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    THREADS = "THREADS"
    PINTEREST = "PINTEREST"
    TIKTOK = "TIKTOK"
    YOUTUBE_COMMUNITY = "YOUTUBE_COMMUNITY"
    YOUTUBE_SHORTS = "YOUTUBE_SHORTS"
    REDDIT = "REDDIT"
    DISCORD = "DISCORD"
    TELEGRAM = "TELEGRAM"
    MEDIUM = "MEDIUM"
    QUORA = "QUORA"


# ─── Content Type Enum ────────────────────────────────────────────────────────

class SocialContentType(str, enum.Enum):
    POST = "POST"
    THREAD = "THREAD"
    CAROUSEL = "CAROUSEL"
    STORY = "STORY"
    REEL = "REEL"
    SHORT = "SHORT"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    LAUNCH_POST = "LAUNCH_POST"
    CASE_STUDY = "CASE_STUDY"
    TESTIMONIAL = "TESTIMONIAL"
    POLL = "POLL"
    QUESTION = "QUESTION"
    MEME = "MEME"
    EDUCATIONAL = "EDUCATIONAL"
    PRODUCT_UPDATE = "PRODUCT_UPDATE"
    HIRING_POST = "HIRING_POST"
    COMMUNITY_POST = "COMMUNITY_POST"
    NEWSLETTER_PROMO = "NEWSLETTER_PROMO"
    EVENT_PROMO = "EVENT_PROMO"
    BLOG_PROMO = "BLOG_PROMO"


# ─── Schedule Type Enum ───────────────────────────────────────────────────────

class ScheduleType(str, enum.Enum):
    PUBLISH_NOW = "PUBLISH_NOW"
    SCHEDULED = "SCHEDULED"
    RECURRING = "RECURRING"
    BULK = "BULK"
    DRAFT = "DRAFT"
    QUEUE = "QUEUE"


# ─── Post Status Enum ─────────────────────────────────────────────────────────

class SocialPostStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"
    CANCELLED = "CANCELLED"


# ─── Platform Configurations ──────────────────────────────────────────────────

PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    "LINKEDIN": {
        "char_limit": 3000,
        "hashtag_limit": 5,
        "tone": "professional",
        "emoji_friendly": False,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_polls": True,
        "best_post_length": 1500,
        "cta_style": "professional",
        "image_ratio": "1:1",
        "best_practices": [
            "Lead with a strong hook in the first line",
            "Use line breaks to improve readability",
            "Tag relevant people and companies",
            "End with a question to drive comments",
            "Post on Tuesday–Thursday 8–10 AM",
        ],
        "image_spec": {"width": 1200, "height": 627},
    },
    "TWITTER": {
        "char_limit": 280,
        "hashtag_limit": 2,
        "tone": "concise",
        "emoji_friendly": True,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": False,
        "supports_polls": True,
        "best_post_length": 240,
        "cta_style": "direct",
        "image_ratio": "16:9",
        "best_practices": [
            "Front-load the most important information",
            "Use threads for longer content",
            "2 hashtags maximum",
            "Add image for 3x engagement",
            "Post during commute hours 7–9 AM or 5–7 PM",
        ],
        "image_spec": {"width": 1600, "height": 900},
    },
    "FACEBOOK": {
        "char_limit": 63206,
        "hashtag_limit": 3,
        "tone": "community",
        "emoji_friendly": True,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_polls": True,
        "best_post_length": 500,
        "cta_style": "community",
        "image_ratio": "1.91:1",
        "best_practices": [
            "Ask questions to encourage sharing",
            "Keep captions under 80 characters for mobile",
            "Use video for highest organic reach",
            "Respond to every comment in the first hour",
            "Post on Wednesday 11 AM – 1 PM",
        ],
        "image_spec": {"width": 1200, "height": 630},
    },
    "INSTAGRAM": {
        "char_limit": 2200,
        "hashtag_limit": 30,
        "tone": "visual",
        "emoji_friendly": True,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_polls": True,
        "best_post_length": 300,
        "cta_style": "visual",
        "image_ratio": "1:1",
        "best_practices": [
            "Lead with the most important text before 'more'",
            "Use 15–30 relevant hashtags",
            "Add 3–5 emojis for personality",
            "Use carousel for 3x engagement",
            "Post on Monday–Friday 9 AM, 12 PM, or 5 PM",
        ],
        "image_spec": {"width": 1080, "height": 1080},
    },
    "THREADS": {
        "char_limit": 500,
        "hashtag_limit": 3,
        "tone": "casual",
        "emoji_friendly": True,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": False,
        "supports_polls": False,
        "best_post_length": 400,
        "cta_style": "conversational",
        "image_ratio": "1:1",
        "best_practices": [
            "Be authentic and conversational",
            "Ask questions or share opinions",
            "Short sentences work best",
            "Cross-post from Instagram strategically",
        ],
        "image_spec": {"width": 1080, "height": 1080},
    },
    "PINTEREST": {
        "char_limit": 500,
        "hashtag_limit": 20,
        "tone": "inspirational",
        "emoji_friendly": False,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_polls": False,
        "best_post_length": 200,
        "cta_style": "inspirational",
        "image_ratio": "2:3",
        "best_practices": [
            "Use vertical images (2:3 ratio)",
            "Include keywords in description for SEO",
            "Link to relevant landing pages",
            "Rich pins increase click-through rates",
            "Post 10–25 pins per day",
        ],
        "image_spec": {"width": 1000, "height": 1500},
    },
    "TIKTOK": {
        "char_limit": 2200,
        "hashtag_limit": 5,
        "tone": "entertaining",
        "emoji_friendly": True,
        "supports_images": False,
        "supports_video": True,
        "supports_carousel": False,
        "supports_polls": False,
        "best_post_length": 300,
        "cta_style": "entertainment",
        "image_ratio": "9:16",
        "best_practices": [
            "Hook in the first 3 seconds",
            "Use trending audio",
            "Add text overlays for silent viewers",
            "Call to action in the last 3 seconds",
            "Post 1–4 times per day consistently",
        ],
        "image_spec": {"width": 1080, "height": 1920},
    },
    "YOUTUBE_COMMUNITY": {
        "char_limit": 5000,
        "hashtag_limit": 3,
        "tone": "educational",
        "emoji_friendly": True,
        "supports_images": True,
        "supports_video": False,
        "supports_carousel": False,
        "supports_polls": True,
        "best_post_length": 500,
        "cta_style": "subscribe",
        "image_ratio": "16:9",
        "best_practices": [
            "Tease upcoming video content",
            "Use polls to engage subscribers",
            "Share behind-the-scenes content",
            "Post 2–3 times per week",
        ],
        "image_spec": {"width": 1280, "height": 720},
    },
    "YOUTUBE_SHORTS": {
        "char_limit": 5000,
        "hashtag_limit": 3,
        "tone": "entertaining",
        "emoji_friendly": True,
        "supports_images": False,
        "supports_video": True,
        "supports_carousel": False,
        "supports_polls": False,
        "best_post_length": 200,
        "cta_style": "subscribe",
        "image_ratio": "9:16",
        "best_practices": [
            "Keep under 60 seconds",
            "Strong visual hook in first second",
            "Add SEO-rich title and description",
            "#Shorts hashtag required",
        ],
        "image_spec": {"width": 1080, "height": 1920},
    },
    "REDDIT": {
        "char_limit": 40000,
        "hashtag_limit": 0,
        "tone": "authentic",
        "emoji_friendly": False,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": False,
        "supports_polls": True,
        "best_post_length": 1000,
        "cta_style": "discussion",
        "image_ratio": "1:1",
        "best_practices": [
            "No promotional language — be genuinely helpful",
            "Follow subreddit rules strictly",
            "Engage in comments for visibility",
            "Post to relevant subreddits only",
            "Value-first, brand second",
        ],
        "image_spec": {"width": 1200, "height": 1200},
    },
    "DISCORD": {
        "char_limit": 2000,
        "hashtag_limit": 0,
        "tone": "community",
        "emoji_friendly": True,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": False,
        "supports_polls": False,
        "best_post_length": 500,
        "cta_style": "community",
        "image_ratio": "1:1",
        "best_practices": [
            "Post in the correct channel",
            "Use @mentions for relevant members",
            "Embed images for rich posts",
            "Encourage discussion with questions",
        ],
        "image_spec": {"width": 1200, "height": 1200},
    },
    "TELEGRAM": {
        "char_limit": 4096,
        "hashtag_limit": 5,
        "tone": "direct",
        "emoji_friendly": True,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": False,
        "supports_polls": True,
        "best_post_length": 800,
        "cta_style": "direct",
        "image_ratio": "1:1",
        "best_practices": [
            "Use markdown formatting for readability",
            "Pin important announcements",
            "Use bots for interactive engagement",
            "Keep announcement channels low-volume",
        ],
        "image_spec": {"width": 1280, "height": 720},
    },
    "MEDIUM": {
        "char_limit": 100000,
        "hashtag_limit": 5,
        "tone": "thought_leadership",
        "emoji_friendly": False,
        "supports_images": True,
        "supports_video": False,
        "supports_carousel": False,
        "supports_polls": False,
        "best_post_length": 5000,
        "cta_style": "editorial",
        "image_ratio": "16:9",
        "best_practices": [
            "Include a compelling subtitle",
            "Use header images for each section",
            "Link to external sources for credibility",
            "Minimum 5-minute read time",
            "Add to relevant publications for distribution",
        ],
        "image_spec": {"width": 1400, "height": 787},
    },
    "QUORA": {
        "char_limit": 10000,
        "hashtag_limit": 0,
        "tone": "expert",
        "emoji_friendly": False,
        "supports_images": True,
        "supports_video": False,
        "supports_carousel": False,
        "supports_polls": False,
        "best_post_length": 800,
        "cta_style": "expert",
        "image_ratio": "1:1",
        "best_practices": [
            "Answer questions you genuinely know",
            "Cite data and sources",
            "Use images to illustrate points",
            "Avoid promotional language",
            "Provide actionable value first",
        ],
        "image_spec": {"width": 1200, "height": 1200},
    },
}


# ─── SSE Event Names ──────────────────────────────────────────────────────────

SOCIAL_SSE_EVENTS: List[str] = [
    "planning",
    "brand",
    "campaign",
    "knowledge",
    "content",
    "image",
    "hashtags",
    "optimization",
    "reflection",
    "evaluation",
    "schedule",
    "publish",
    "completed",
    "error",
    "status",
]


# ─── Default Provider Priority ────────────────────────────────────────────────

DEFAULT_PROVIDER_PRIORITY: List[str] = [
    "groq",
    "openai",
    "google",
    "anthropic",
    "openrouter",
]

SUPPORTED_MODELS: List[str] = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-5-sonnet-20241022",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
]


# ─── Engagement Content Types ─────────────────────────────────────────────────

class EngagementType(str, enum.Enum):
    REPLY = "REPLY"
    COMMENT = "COMMENT"
    DM_DRAFT = "DM_DRAFT"
    COMMUNITY_REPLY = "COMMUNITY_REPLY"
    FAQ_REPLY = "FAQ_REPLY"
    THANK_YOU = "THANK_YOU"


# ─── Analytics Metrics ────────────────────────────────────────────────────────

ANALYTICS_METRICS: List[str] = [
    "reach",
    "impressions",
    "likes",
    "shares",
    "comments",
    "clicks",
    "ctr",
    "conversions",
    "followers",
    "engagement_rate",
]


# ─── Image Types per Platform ─────────────────────────────────────────────────

PLATFORM_IMAGE_TYPES: Dict[str, List[str]] = {
    "INSTAGRAM": ["square", "portrait", "landscape", "story", "carousel"],
    "LINKEDIN": ["banner", "post", "article_cover"],
    "FACEBOOK": ["post", "cover", "ad", "story"],
    "PINTEREST": ["pin", "story_pin", "idea_pin"],
    "TIKTOK": ["thumbnail", "cover"],
    "YOUTUBE_SHORTS": ["thumbnail"],
    "YOUTUBE_COMMUNITY": ["post_image"],
    "TWITTER": ["post", "card", "header"],
    "THREADS": ["post"],
    "REDDIT": ["post_image", "banner"],
    "DISCORD": ["post"],
    "TELEGRAM": ["post"],
    "MEDIUM": ["cover", "inline"],
    "QUORA": ["inline"],
}


# ─── Publisher Adapter Registry ───────────────────────────────────────────────

PUBLISHER_REGISTRY: Dict[str, str] = {
    "LINKEDIN": "LinkedInPublisher",
    "TWITTER": "TwitterPublisher",
    "FACEBOOK": "FacebookPublisher",
    "INSTAGRAM": "InstagramPublisher",
    "PINTEREST": "PinterestPublisher",
    "YOUTUBE_COMMUNITY": "YouTubePublisher",
    "YOUTUBE_SHORTS": "YouTubePublisher",
    "THREADS": "ThreadsPublisher",
}


# ─── Hashtag Industry Categories ─────────────────────────────────────────────

INDUSTRY_HASHTAG_POOLS: Dict[str, List[str]] = {
    "saas": ["#SaaS", "#B2BSaaS", "#ProductLed", "#StartupLife", "#TechStartup"],
    "marketing": ["#DigitalMarketing", "#ContentMarketing", "#MarketingTips", "#GrowthHacking", "#SEO"],
    "ai": ["#AI", "#ArtificialIntelligence", "#MachineLearning", "#GenerativeAI", "#LLM"],
    "startup": ["#Startup", "#Founder", "#Bootstrap", "#VentureCapital", "#Entrepreneurship"],
    "design": ["#UIDesign", "#UXDesign", "#ProductDesign", "#DesignThinking", "#Figma"],
    "sales": ["#Sales", "#SalesStrategy", "#B2BSales", "#ColdOutreach", "#Pipeline"],
    "ecommerce": ["#Ecommerce", "#DTC", "#Shopify", "#OnlineBusiness", "#DropShipping"],
    "content": ["#ContentCreator", "#Blogging", "#Copywriting", "#ContentStrategy", "#WritingTips"],
    "leadership": ["#Leadership", "#Management", "#ExecutiveMindset", "#BusinessGrowth", "#Strategy"],
    "productivity": ["#Productivity", "#RemoteWork", "#WorkFromHome", "#TimeManagement", "#Efficiency"],
}
