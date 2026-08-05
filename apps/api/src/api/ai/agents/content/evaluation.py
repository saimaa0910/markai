"""
Content Agent Evaluation & SEO Engine — Sprint 7.2
===================================================
Local scoring engine calculating keyword densities, reading difficulty index
(Flesch-Kincaid Ease index approximation), heading counts, and metadata constraints.
"""
import re
from typing import List, Dict, Any, Optional
from api.ai.agents.content.constants import SEO_TARGETS, READABILITY_THRESHOLDS
from api.ai.agents.content.schemas import ContentSEOMetrics


def _calculate_flesch_reading_ease(text: str) -> float:
    """
    Approximate Flesch Reading Ease score.
    Formula: 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    """
    clean = re.sub(r'[^\w\s\.\!\?]', '', text)
    words = clean.split()
    word_count = len(words)
    if word_count == 0:
        return 100.0

    # Sentences count
    sentences = re.split(r'[\.\!\?]+', text)
    sentence_count = max(1, len([s for s in sentences if s.strip()]))

    # Syllables count (approximate using vowels clusters)
    syllable_count = 0
    for word in words:
        word = word.lower()
        # count vowel groups
        vowels = "aeiouy"
        count = 0
        if not word:
            continue
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        syllable_count += count

    asl = word_count / sentence_count
    asw = syllable_count / word_count
    
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return max(0.0, min(100.0, score))


class ContentEvaluator:
    """Scoring engine evaluating grammar, readability, links, and SEO factors."""

    @staticmethod
    def evaluate_seo(
        content: str,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        meta_desc: Optional[str] = None,
    ) -> ContentSEOMetrics:
        """
        Evaluate generated content against SEO rules and readability benchmarks.
        Does not require LLM calls.
        """
        suggestions: List[str] = []
        
        # Word count
        word_count = len(content.split())
        
        # 1. Meta Length Checks
        title_ok = True
        if title:
            t_len = len(title)
            if t_len < SEO_TARGETS["title_min_length"] or t_len > SEO_TARGETS["title_max_length"]:
                title_ok = False
                suggestions.append(f"Adjust SEO Title length ({t_len} chars). Target: {SEO_TARGETS['title_min_length']}-{SEO_TARGETS['title_max_length']} chars.")
                
        desc_ok = True
        if meta_desc:
            d_len = len(meta_desc)
            if d_len < SEO_TARGETS["desc_min_length"] or d_len > SEO_TARGETS["desc_max_length"]:
                desc_ok = False
                suggestions.append(f"Adjust Meta Description length ({d_len} chars). Target: {SEO_TARGETS['desc_min_length']}-{SEO_TARGETS['desc_max_length']} chars.")

        # 2. Keyword Density
        density_map = {}
        density_ok = True
        if keywords and word_count > 0:
            for kw in keywords:
                if not kw:
                    continue
                # count case-insensitive occurrences
                pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                matches = len(pattern.findall(content))
                density = matches / word_count
                density_map[kw] = round(density, 4)
                
                if density < SEO_TARGETS["min_keyword_density"]:
                    density_ok = False
                    suggestions.append(f"Keyword '{kw}' density is low ({density*100:.2f}%). Try mentioning it more often.")
                elif density > SEO_TARGETS["max_keyword_density"]:
                    density_ok = False
                    suggestions.append(f"Keyword '{kw}' density is high ({density*100:.2f}%). Avoid keyword stuffing.")

        # 3. Heading Structure
        h1_count = len(re.findall(r"^#\s+", content, re.MULTILINE)) + len(re.findall(r"<h1\b", content, re.IGNORECASE))
        h2_count = len(re.findall(r"^##\s+", content, re.MULTILINE)) + len(re.findall(r"<h2\b", content, re.IGNORECASE))
        heading_hierarchy_ok = True
        if h1_count > 1:
            heading_hierarchy_ok = False
            suggestions.append("Multiple H1 tags detected. Use only one H1 tag per page.")
        if h1_count == 0:
            suggestions.append("No H1 tag detected. Consider adding a main header.")
        if h2_count == 0 and word_count > 300:
            suggestions.append("No H2 headings detected. Break up long copy with subheadings.")

        # 4. Links Count
        # Markdown links [anchor](url)
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        # HTML links <a href=
        html_links = re.findall(r"<a\s+(?:[^>]*?\s+)?href=([\"'])(.*?)\1", content, re.IGNORECASE)
        
        internal_links = 0
        external_links = 0
        
        all_links_urls = [l[1] for l in md_links] + [l[1] for l in html_links]
        for url in all_links_urls:
            if url.startswith("/") or "markai" in url or "eaimos" in url:
                internal_links += 1
            else:
                external_links += 1
                
        if internal_links == 0:
            suggestions.append("No internal links found. Link to other resources on your site.")

        # 5. Readability
        readability = _calculate_flesch_reading_ease(content)
        readability_level = "MEDIUM"
        for level, (low, high) in READABILITY_THRESHOLDS.items():
            if low <= readability <= high:
                readability_level = level
                break
                
        if readability < 40.0:
            suggestions.append("Reading level is difficult. Try using shorter sentences and simpler vocabulary.")

        # Compute Overall SEO Score (0.0 to 1.0)
        score_base = 1.0
        if not title_ok: score_base -= 0.15
        if not desc_ok: score_base -= 0.15
        if not density_ok: score_base -= 0.20
        if not heading_hierarchy_ok: score_base -= 0.15
        if internal_links == 0: score_base -= 0.10
        if readability < 50.0: score_base -= 0.15
        if word_count < 100: score_base -= 0.10
        
        seo_score = max(0.0, min(1.0, score_base))

        return ContentSEOMetrics(
            title_length_ok=title_ok,
            description_length_ok=desc_ok,
            keyword_density=density_map,
            keyword_density_ok=density_ok,
            heading_hierarchy_ok=heading_hierarchy_ok,
            readability_score=round(readability, 2),
            readability_level=readability_level,
            internal_links_count=internal_links,
            external_links_count=external_links,
            seo_score=round(seo_score, 2),
            suggestions=suggestions,
        )
