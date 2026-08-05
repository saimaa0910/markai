"""
Content Agent Prompt Templates — Sprint 7.2
============================================
Defines reusable, dynamic prompts for 25+ content types and 11+ improvement rules.
"""
from typing import Dict, List, Optional, Any
from api.ai.agents.content.constants import ContentType, ImprovementType

# Reusable templates for various Content Types
CONTENT_TEMPLATES: Dict[ContentType, str] = {
    ContentType.BLOG_ARTICLE: (
        "Write a structured, engaging blog article. "
        "Include a compelling title, introduction with a hook, subheadings (H2, H3), "
        "and a concluding section with a strong call-to-action.\n"
        "Requirements:\n"
        "- Audience: {audience}\n"
        "- Target SEO keywords: {keywords}\n"
        "- Prompt instructions: {prompt}\n"
    ),
    ContentType.LANDING_PAGE: (
        "Create copy for a high-converting landing page. "
        "Provide: Headline (Hero section), Sub-headline, Key benefits/features bullet points, "
        "Social proof/testimonial sections, and Primary call-to-action (CTA) text.\n"
        "Requirements:\n"
        "- Audience: {audience}\n"
        "- Keywords: {keywords}\n"
        "- Instructions: {prompt}\n"
    ),
    ContentType.PRODUCT_PAGE: (
        "Write copy for a product detail page. "
        "Include a catchy product title, a summary description, key benefits/specifications list, "
        "and buying call-to-action (CTA).\n"
        "Requirements:\n"
        "- Audience: {audience}\n"
        "- Prompt: {prompt}\n"
    ),
    ContentType.EMAIL_CAMPAIGN: (
        "Write a high-converting marketing email campaign. "
        "Provide 3 subject line options, preview text, email body, and a clear call-to-action (CTA).\n"
        "Requirements:\n"
        "- Audience: {audience}\n"
        "- Instructions: {prompt}\n"
    ),
    ContentType.NEWSLETTER: (
        "Draft an engaging, informational company newsletter. "
        "Include an opening greeting, 2-3 short news or educational blocks, "
        "and a link placeholder/call-to-action.\n"
        "Requirements:\n"
        "- Instructions: {prompt}\n"
    ),
    ContentType.LINKEDIN_POST: (
        "Write a professional LinkedIn post. "
        "Start with an attention-grabbing hook, tell a brief story or provide key bullet-point takeaways, "
        "and end with a discussion question to invite comments. Keep it under 250 words and use 3 relevant hashtags.\n"
        "Requirements:\n"
        "- Instructions: {prompt}\n"
    ),
    ContentType.TWITTER_POST: (
        "Draft a compelling, concise tweet (under 280 characters) with 1-2 hashtags.\n"
        "Requirements:\n"
        "- Instructions: {prompt}\n"
    ),
    ContentType.GOOGLE_AD: (
        "Create Google Search Ad copy. "
        "Provide 3 headline options (under 30 chars each) and 2 description options (under 90 chars each).\n"
        "Requirements:\n"
        "- Target Keywords: {keywords}\n"
        "- Product Details: {prompt}\n"
    ),
    ContentType.META_DESCRIPTION: (
        "Generate a search engine optimized meta description (120-150 characters) "
        "incorporating the target keywords.\n"
        "Requirements:\n"
        "- Target Keywords: {keywords}\n"
        "- Subject: {prompt}\n"
    ),
    ContentType.IMAGE_PROMPT: (
        "Write a highly descriptive, detailed prompt for generating an image with Midjourney, DALL-E, or Stable Diffusion. "
        "Specify the style, composition, lighting, color palette, and subject details.\n"
        "Requirements:\n"
        "- Subject/Concept: {prompt}\n"
    ),
}

# Fallback template for any other Content Type
DEFAULT_CONTENT_TEMPLATE = (
    "Create {content_type} content according to these requirements:\n"
    "- Target Audience: {audience}\n"
    "- Target SEO Keywords: {keywords}\n"
    "- Guidelines: {prompt}\n"
)

# Reusable templates for Content Improvement
IMPROVEMENT_TEMPLATES: Dict[ImprovementType, str] = {
    ImprovementType.REWRITE: (
        "Rewrite the following content to make it fresh and engaging while keeping the original meaning intact:\n\n"
        "{content}"
    ),
    ImprovementType.SUMMARIZE: (
        "Provide a concise summary of the following text, highlighting all key takeaways and major points:\n\n"
        "{content}"
    ),
    ImprovementType.EXPAND: (
        "Elaborate on the following text by adding depth, examples, and relevant details. Make it richer:\n\n"
        "{content}"
    ),
    ImprovementType.SHORTEN: (
        "Trim and edit the following content to be direct and concise. Remove fluff while retaining core information:\n\n"
        "{content}"
    ),
    ImprovementType.IMPROVE_GRAMMAR: (
        "Proofread and correct any grammatical errors, spelling mistakes, or awkward phrasing in this text. "
        "Return the polished version:\n\n"
        "{content}"
    ),
    ImprovementType.IMPROVE_SEO: (
        "Optimize the following content for search engines (SEO). Incorporate the target keywords naturally, "
        "and suggest search-friendly structural updates (e.g. headers):\n"
        "Keywords: {keywords}\n\n"
        "Content:\n{content}"
    ),
    ImprovementType.IMPROVE_READABILITY: (
        "Simplify the style and syntax of the following content to make it much easier to read and understand:\n\n"
        "{content}"
    ),
    ImprovementType.IMPROVE_BRAND_VOICE: (
        "Align the following content with our brand voice guidelines: {brand_voice}\n\n"
        "Content:\n{content}"
    ),
    ImprovementType.TRANSLATE: (
        "Translate the following text into target language: {target_language}. Maintain the tone and context:\n\n"
        "{content}"
    ),
    ImprovementType.TONE_CONVERSION: (
        "Convert the tone of this content to be {target_tone} (e.g., professional, playful, empathetic):\n\n"
        "{content}"
    ),
    ImprovementType.AUDIENCE_CONVERSION: (
        "Adapt this content for a different target audience: {target_audience}:\n\n"
        "{content}"
    ),
}


def get_content_prompt(
    content_type: ContentType,
    prompt: str,
    audience: Optional[str] = None,
    keywords: Optional[List[str]] = None,
) -> str:
    """Resolve and build the content generation prompt template."""
    template = CONTENT_TEMPLATES.get(content_type, DEFAULT_CONTENT_TEMPLATE)
    
    aud_str = audience or "General Audience"
    kw_str = ", ".join(keywords) if keywords else "None specified"
    
    return template.format(
        content_type=content_type.value if hasattr(content_type, "value") else str(content_type),
        audience=aud_str,
        keywords=kw_str,
        prompt=prompt,
    )


def get_improvement_prompt(
    improvement_type: ImprovementType,
    content: str,
    brand_voice: Optional[str] = None,
    target_language: Optional[str] = None,
    target_tone: Optional[str] = None,
    target_audience: Optional[str] = None,
    keywords: Optional[List[str]] = None,
) -> str:
    """Resolve and build the improvement prompt template."""
    template = IMPROVEMENT_TEMPLATES.get(improvement_type)
    if not template:
        raise ValueError(f"Unknown improvement type: {improvement_type}")
        
    kw_str = ", ".join(keywords) if keywords else "None specified"
    
    return template.format(
        content=content,
        brand_voice=brand_voice or "Professional, clear, engaging.",
        target_language=target_language or "English",
        target_tone=target_tone or "Professional",
        target_audience=target_audience or "General Audience",
        keywords=kw_str,
    )


def build_brand_voice_instruction(
    brand_voice: Optional[str] = None,
    preferred_words: Optional[List[str]] = None,
    forbidden_words: Optional[List[str]] = None,
) -> str:
    """Construct prompt formatting guidelines for brand voice settings."""
    instructions = []
    if brand_voice:
        instructions.append(f"BRAND VOICE & STYLE:\n{brand_voice}")
        
    if preferred_words:
        words_str = ", ".join([f"'{w}'" for w in preferred_words])
        instructions.append(f"PREFERRED VOCABULARY:\nTry to naturally incorporate the following words/phrases: {words_str}")
        
    if forbidden_words:
        words_str = ", ".join([f"'{w}'" for w in forbidden_words])
        instructions.append(f"FORBIDDEN WORDS (CRITICAL):\nDo NOT use the following words or any close variations: {words_str}")
        
    return "\n\n".join(instructions) if instructions else ""


def list_templates() -> List[Dict[str, Any]]:
    """List details of all built-in content templates."""
    templates = []
    for c_type, template_text in CONTENT_TEMPLATES.items():
        variables = []
        if "{audience}" in template_text:
            variables.append("audience")
        if "{keywords}" in template_text:
            variables.append("keywords")
        if "{prompt}" in template_text:
            variables.append("prompt")
            
        templates.append({
            "id": c_type.name.lower(),
            "name": c_type.value.replace("_", " ").title(),
            "description": f"Generate content optimized for {c_type.value}",
            "content_type": c_type,
            "template_text": template_text,
            "required_variables": variables,
        })
    return templates
