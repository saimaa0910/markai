"""
Tests: Brand Voice Engine — Sprint 7.2
========================================
Verifies prompt construction from brand guidelines and dynamic vocabulary fields.
"""
from api.ai.agents.content.prompts import build_brand_voice_instruction


class TestBrandVoiceEngine:

    def test_build_brand_voice_with_all_parameters(self):
        brand_voice = "Bold, energetic, and data-driven."
        preferred_words = ["efficiency", "ROI", "automation"]
        forbidden_words = ["disruptive", "paradigm shift"]

        instruction = build_brand_voice_instruction(
            brand_voice=brand_voice,
            preferred_words=preferred_words,
            forbidden_words=forbidden_words,
        )

        assert "Bold, energetic, and data-driven." in instruction
        assert "efficiency" in instruction
        assert "ROI" in instruction
        assert "disruptive" in instruction
        assert "FORBIDDEN" in instruction

    def test_build_brand_voice_empty_inputs(self):
        instruction = build_brand_voice_instruction(None, None, None)
        assert instruction == ""
        
    def test_build_brand_voice_only_voice(self):
        instruction = build_brand_voice_instruction("Professional style.", None, None)
        assert "Professional style." in instruction
        assert "PREFERRED" not in instruction
        assert "FORBIDDEN" not in instruction
