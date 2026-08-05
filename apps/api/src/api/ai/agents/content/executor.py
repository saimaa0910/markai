"""
Content Agent Executor — Sprint 7.2
=====================================
Executes the generated content plan. Integrates Brand Voice,
RAG search (Knowledge Platform), AIGateway chat generation,
ContentReflector self-correction, and ContentEvaluator scoring.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api.ai.agents.content.constants import ContentType, ImprovementType
from api.ai.agents.content.prompts import (
    get_content_prompt, get_improvement_prompt,
    build_brand_voice_instruction
)
from api.ai.agents.content.tools import ContentAgentTools
from api.ai.agents.content.planner import ContentPlanner
from api.ai.agents.content.reflection import ContentReflector
from api.ai.agents.content.evaluation import ContentEvaluator
from api.ai.gateway.coordinator import AIGateway
from api.services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ContentExecutor:
    """Coordinates brand checks, RAG contexts, LLM invocations, reflection, and SEO metrics."""

    def __init__(self, db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
        self.gateway = AIGateway()
        self.tools_wrapper = ContentAgentTools(db, org_id, user_id)
        self.reflector = ContentReflector()

    def generate(
        self,
        content_type: ContentType,
        prompt: str,
        brand_voice_override: Optional[str] = None,
        forbidden_words: Optional[List[str]] = None,
        preferred_words: Optional[List[str]] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        target_audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.7,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Dict[str, Any]:
        """Generate content from scratch using prompts, RAG search, reflection, and SEO evaluation."""
        
        # 1. Fetch Brand voice guidelines from organization memories if not overridden
        brand_voice = brand_voice_override
        if not brand_voice:
            org_memories = MemoryManager.get_org_memory(self.db, self.org_id)
            voice_items = [m.value for m in org_memories if m.category == "brand_voice" or m.key == "brand_voice"]
            brand_voice = "\n".join(voice_items) if voice_items else "Professional, clear, engaging."

        # 2. Query RAG (RAG search) if collection IDs are provided
        rag_chunks = []
        if knowledge_collections:
            search_query = f"{prompt} {', '.join(keywords or [])}"
            rag_chunks = self.tools_wrapper.search_knowledge(
                query=search_query,
                collection_ids=knowledge_collections,
                limit=3
            )

        # 3. Build prompts
        base_prompt = get_content_prompt(
            content_type=content_type,
            prompt=prompt,
            audience=target_audience,
            keywords=keywords,
        )
        
        brand_instruction = build_brand_voice_instruction(
            brand_voice=brand_voice,
            preferred_words=preferred_words,
            forbidden_words=forbidden_words,
        )
        
        system_instruction = "You are a professional Enterprise Content Writer.\n"
        if brand_instruction:
            system_instruction += f"\n{brand_instruction}\n"
        if rag_chunks:
            system_instruction += "\n=== RELEVANT CONTEXT (CITE SOURCES WHEN APPROPRIATE) ===\n"
            system_instruction += "\n\n".join(rag_chunks)
            system_instruction += "\n=======================================================\n"

        # 4. Generate trace plan
        plan = ContentPlanner.generate_plan(
            content_type=content_type,
            prompt=prompt,
            audience=target_audience,
            keywords=keywords,
            has_collections=bool(knowledge_collections),
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": base_prompt},
        ]

        # 5. Execute LLM pass
        logger.info("Executing initial generation pass...")
        import time
        start_time = time.perf_counter()
        
        gw_result = self.gateway.chat(
            db=self.db,
            messages=messages,
            organization_id=self.org_id,
            user_id=self.user_id,
            model_name=preferred_model,
            temperature=temperature,
        )
        
        raw_content = gw_result.get("content", "")
        prompt_tokens = gw_result.get("prompt_tokens", 0)
        completion_tokens = gw_result.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens

        # 6. Reflection self-correction loop
        reflection_passed = True
        critique = None
        suggested_edits = None
        
        if run_reflection and raw_content:
            raw_content, reflection, attempts = self.reflector.review_and_correct(
                db=self.db,
                prompt=prompt,
                content=raw_content,
                organization_id=self.org_id,
                user_id=self.user_id,
                brand_voice=brand_voice,
                model_name=preferred_model,
            )
            reflection_passed = reflection.is_satisfactory
            critique = reflection.critique
            suggested_edits = reflection.suggested_edits

        # 7. SEO and readability evaluation
        seo_metrics = None
        if run_evaluation and raw_content:
            seo_metrics = ContentEvaluator.evaluate_seo(
                content=raw_content,
                keywords=keywords,
                title=prompt[:40],
                meta_desc=prompt[:120],
            )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Output results
        return {
            "title": prompt[:60],
            "generated_content": raw_content,
            "plan": plan,
            "tool_calls": plan.get("steps", []),
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "cost_usd": float(total_tokens * 0.000002), # Approximate token cost
            "seo_metrics": seo_metrics,
            "overall_score": seo_metrics.seo_score if seo_metrics else 1.0,
            "reflection_passed": reflection_passed,
            "critique": critique,
            "suggested_edits": suggested_edits,
        }

    def improve(
        self,
        content: str,
        improvement_type: ImprovementType,
        target_tone: Optional[str] = None,
        target_audience: Optional[str] = None,
        target_language: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.5,
    ) -> str:
        """Improve existing content using editing, translation, or rewriting prompts."""
        
        # Build prompt
        prompt = get_improvement_prompt(
            improvement_type=improvement_type,
            content=content,
            target_language=target_language,
            target_tone=target_tone,
            target_audience=target_audience,
            keywords=keywords,
        )

        gw_result = self.gateway.chat(
            db=self.db,
            messages=[{"role": "user", "content": prompt}],
            organization_id=self.org_id,
            user_id=self.user_id,
            model_name=preferred_model,
            temperature=temperature,
        )
        return gw_result.get("content", "")
