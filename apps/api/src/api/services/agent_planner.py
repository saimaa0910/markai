import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from api.ai.gateway.coordinator import AIGateway
from api.models.agent import AgentDefinition
from api.services.memory_manager import MemoryManager


class AgentPlannerService:
    """
    LLM-based planning service for generating agent execution plans.
    Given user input, memory, and allowed tools, determines next actions.
    """

    @staticmethod
    def generate_plan(
        db: Session,
        agent: AgentDefinition,
        user_input: str,
        session_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        # 1. Gather context and tools
        memory_context = MemoryManager.build_memory_context(
            db=db,
            agent_id=agent.id,
            organization_id=organization_id,
            session_id=session_id,
        )

        from api.ai.tools.registry import ToolRegistry
        allowed_tools = agent.allowed_tools or []
        tools_schemas = ToolRegistry.to_openai_functions(allowed_tools)

        # 2. Formulate System Instruction
        system_instruction = (
            f"You are {agent.name}, an expert AI Agent specializing in {agent.agent_type.value}.\n"
            f"Description: {agent.description or 'No description provided.'}\n\n"
            f"System Prompt:\n{agent.system_prompt or 'Address the user request professionally.'}\n\n"
            f"Below is the current context including memory:\n"
            f"{memory_context}\n\n"
            f"Available tools you can request in your plan:\n"
            f"{str(tools_schemas)}\n\n"
            f"Create a JSON execution plan specifying your next thought and the list of tool execution steps to run.\n"
            f"If you can answer directly without tools, return an empty steps list."
        )

        # 3. Request structured JSON from AI Gateway
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_input},
        ]

        schema = {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Your internal thought process on how to achieve the goal.",
                },
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_id": {"type": "string", "description": "Unique identifier for this step, e.g. step_1"},
                            "tool_name": {"type": "string", "description": "The name of the tool to invoke"},
                            "tool_params": {
                                "type": "object",
                                "description": "A dictionary of key-value parameters matching the tool's parameters schema",
                            },
                            "description": {"type": "string", "description": "Short explanation of why you are invoking this tool"},
                        },
                        "required": ["step_id", "tool_name", "tool_params"],
                    },
                },
            },
            "required": ["thought", "steps"],
        }

        gateway = AIGateway()
        try:
            plan_response = gateway.json_output(
                db=db,
                messages=messages,
                schema=schema,
                organization_id=organization_id,
                user_id=user_id,
            )
            return plan_response
        except Exception as e:
            # Fallback simple direct plan on gateway failure or routing problems
            return {
                "thought": f"Encountered planning exception: {str(e)}. Attempting direct resolution.",
                "steps": []
            }
