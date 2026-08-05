"""
Content Agent Planner — Sprint 7.2
====================================
Analyzes content goals, target audience, and creates a step-by-step plan
identifying required RAG collections and tool execution sequences.
"""
from typing import Dict, Any, List, Optional
from api.ai.agents.content.constants import ContentType


class ContentPlanner:
    """Creates structured content generation plans based on input goals."""

    @staticmethod
    def generate_plan(
        content_type: ContentType,
        prompt: str,
        audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        has_collections: bool = False,
    ) -> Dict[str, Any]:
        """
        Formulate a step-by-step planning blueprint.
        Ensures execution timeline is fully transparent.
        """
        target_audience = audience or "General Audience"
        kw_list = keywords or []
        
        thought = (
            f"Planning content generation for a '{content_type.value}' targeted at '{target_audience}'. "
            f"The goal is to draft copy about '{prompt[:100]}...'. "
        )
        if kw_list:
            thought += f"Optimizing structure and density for keywords: {', '.join(kw_list)}."
            
        steps = []
        step_index = 1

        # Step 1: Knowledge Gathering
        if has_collections:
            steps.append({
                "step_id": f"step_{step_index}",
                "tool_name": "knowledge_tool",
                "tool_params": {
                    "query": prompt[:150],
                    "limit": 3
                },
                "description": "Retrieve product and brand guidelines from selected knowledge collections."
            })
            step_index += 1
            
        # Step 2: Context Construction
        steps.append({
            "step_id": f"step_{step_index}",
            "tool_name": "calculator_tool",
            "tool_params": {
                "expression": f"{len(prompt)} / 4"
            },
            "description": "Calculate approximate token allocations for prompt inputs."
        })
        step_index += 1

        # Step 3: Call generation
        steps.append({
            "step_id": f"step_{step_index}",
            "tool_name": "analytics_tool",
            "tool_params": {
                "metric_type": "cost_summary"
            },
            "description": "Verify organization budget limits before issuing LLM generation request."
        })

        return {
            "thought": thought,
            "steps": steps,
            "metadata": {
                "content_type": content_type,
                "audience": target_audience,
                "keywords": kw_list,
            }
        }
