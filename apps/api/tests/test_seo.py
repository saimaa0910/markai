"""
Tests: SEO & Readability Engine — Sprint 7.2
=============================================
Verifies keyword density parsing, heading structure, links checks, and Flesch Reading Ease calculations.
"""
from api.ai.agents.content.evaluation import ContentEvaluator


class TestSEOEngine:

    def test_evaluate_seo_easy_readability(self):
        # Short simple sentence structure is easy to read
        content = "The cat sat on the mat. The dog sat by the door. We like to eat bread."
        keywords = ["cat", "dog"]

        metrics = ContentEvaluator.evaluate_seo(
            content=content,
            keywords=keywords,
            title="A Simple Title That Is Correct Length",
            meta_desc="This is a simple meta description that meets the length check requirements perfectly for test purposes, making it long enough."
        )

        assert metrics.title_length_ok is True
        assert metrics.description_length_ok is True
        assert "cat" in metrics.keyword_density
        assert metrics.keyword_density["cat"] > 0.05
        assert metrics.readability_score > 80.0
        assert metrics.readability_level == "EASY"

    def test_evaluate_seo_heading_hierarchy(self):
        # Multiple H1 headers should flag heading hierarchy
        content = "# Headline 1\n\nContent here.\n\n# Headline 2\n\nMore content."
        
        metrics = ContentEvaluator.evaluate_seo(content=content)
        assert metrics.heading_hierarchy_ok is False
        assert any("Multiple H1" in sug for sug in metrics.suggestions)

    def test_evaluate_seo_links_counting(self):
        content = "Go to [our website](/dashboard/agents) or view [Google](https://google.com)."
        
        metrics = ContentEvaluator.evaluate_seo(content=content)
        assert metrics.internal_links_count == 1
        assert metrics.external_links_count == 1
