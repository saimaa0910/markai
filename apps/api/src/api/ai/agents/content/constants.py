"""
Content Agent Constants — Sprint 7.2
=====================================
Supported Content Types, Content Improvement Types, and default metrics.
"""
import enum


class ContentType(str, enum.Enum):
    # Long-form / Pages
    BLOG_ARTICLE = "BLOG_ARTICLE"
    LANDING_PAGE = "LANDING_PAGE"
    PRODUCT_PAGE = "PRODUCT_PAGE"
    FEATURE_PAGE = "FEATURE_PAGE"
    DOCUMENTATION = "DOCUMENTATION"
    FAQ = "FAQ"
    CASE_STUDY = "CASE_STUDY"
    WHITEPAPER = "WHITEPAPER"
    
    # Emails
    EMAIL_CAMPAIGN = "EMAIL_CAMPAIGN"
    COLD_EMAIL = "COLD_EMAIL"
    NEWSLETTER = "NEWSLETTER"
    
    # Social Media
    LINKEDIN_POST = "LINKEDIN_POST"
    TWITTER_POST = "TWITTER_POST"
    INSTAGRAM_CAPTION = "INSTAGRAM_CAPTION"
    FACEBOOK_POST = "FACEBOOK_POST"
    
    # Ads
    GOOGLE_AD = "GOOGLE_AD"
    FACEBOOK_AD = "FACEBOOK_AD"
    
    # Copywriting Elements
    HEADLINE = "HEADLINE"
    TAGLINE = "TAGLINE"
    CTA = "CTA"
    META_TITLE = "META_TITLE"
    META_DESCRIPTION = "META_DESCRIPTION"
    
    # Scripts & Audio
    VIDEO_SCRIPT = "VIDEO_SCRIPT"
    PODCAST_SCRIPT = "PODCAST_SCRIPT"
    YOUTUBE_DESCRIPTION = "YOUTUBE_DESCRIPTION"
    
    # Assets
    IMAGE_PROMPT = "IMAGE_PROMPT"


class ImprovementType(str, enum.Enum):
    REWRITE = "REWRITE"
    SUMMARIZE = "SUMMARIZE"
    EXPAND = "EXPAND"
    SHORTEN = "SHORTEN"
    IMPROVE_GRAMMAR = "IMPROVE_GRAMMAR"
    IMPROVE_SEO = "IMPROVE_SEO"
    IMPROVE_READABILITY = "IMPROVE_READABILITY"
    IMPROVE_BRAND_VOICE = "IMPROVE_BRAND_VOICE"
    TRANSLATE = "TRANSLATE"
    TONE_CONVERSION = "TONE_CONVERSION"
    AUDIENCE_CONVERSION = "AUDIENCE_CONVERSION"


# Default target boundaries for SEO checking
SEO_TARGETS = {
    "title_min_length": 30,
    "title_max_length": 60,
    "desc_min_length": 110,
    "desc_max_length": 160,
    "min_keyword_density": 0.005,
    "max_keyword_density": 0.035,
}

# Flesch Readability Scoring thresholds
READABILITY_THRESHOLDS = {
    "EASY": (90.0, 100.0),     # 5th grade
    "MEDIUM": (60.0, 89.0),   # 8th-9th grade
    "DIFFICULT": (0.0, 59.0),  # College graduate
}
