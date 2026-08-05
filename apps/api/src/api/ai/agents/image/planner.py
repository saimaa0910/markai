from typing import Dict, Any, List, Optional


class ImagePlanner:
    """Creates step-by-step plans for compiling and executing image generation requests."""

    @staticmethod
    def generate_plan(
        prompt: str,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        campaign_id: Optional[str] = None,
        has_collections: bool = False,
    ) -> Dict[str, Any]:
        """
        Creates a plan listing tools and generation phases.
        """
        target_style = style or "Minimal"
        target_ratio = aspect_ratio or "1:1"
        
        thought = (
            f"Planning visual composition for prompt '{prompt[:80]}...'. "
            f"Style filter selected: '{target_style}' with layout aspect ratio: '{target_ratio}'."
        )
        if campaign_id:
            thought += f" Aligning with campaign rules ID: {campaign_id}."
            
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
                "description": "Extract brand assets and campaign assets from knowledge collections."
            })
            step_index += 1

        # Step 2: Prompt Compilation Placeholder/Action
        steps.append({
            "step_id": f"step_{step_index}",
            "tool_name": "calculator_tool",
            "tool_params": {
                "expression": "1 + 1"
            },
            "description": "Check layout dimensions matching resolution settings."
        })

        return {
            "thought": thought,
            "steps": steps,
            "metadata": {
                "style": target_style,
                "aspect_ratio": target_ratio,
                "campaign_id": campaign_id,
            }
        }
