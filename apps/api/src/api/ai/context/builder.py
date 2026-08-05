"""
Agent Context Builder
=====================
Merges all context sources into a single, token-budgeted context string
ready for injection into the LLM prompt by the Agent Runtime.

Sources merged (in priority order):
  1. System Prompt (agent-level override)
  2. Agent Prompt (from Prompt Platform)
  3. Organization Settings & Brand Voice (OrganizationMemory)
  4. User Profile
  5. Long-Term Agent Memory
  6. Current Session / Conversation Memory
  7. Knowledge retrieval chunks
  8. Tool Results from current run
  9. Workflow State (if applicable)
  10. Current Task / User Input

All existing services are reused — no duplication.
"""
import uuid
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from api.models.agent import AgentDefinition
from api.services.memory_manager import MemoryManager
from api.models.memory import MemoryType

logger = logging.getLogger(__name__)

# Approximate token limit for context (leaves room for user input + completion)
DEFAULT_CONTEXT_TOKEN_BUDGET = 3000
CHARS_PER_TOKEN = 4  # Rough estimate


class ContextBuilder:
    """
    Builds the final agent context string by merging all context sources.
    Respects a token budget to avoid exceeding model context windows.
    """

    def __init__(self, token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET) -> None:
        self.token_budget = token_budget
        self._char_budget = token_budget * CHARS_PER_TOKEN
        self._sections: List[str] = []
        self._char_count = 0

    def _add_section(self, header: str, content: str) -> bool:
        """
        Add a context section if budget allows.
        Returns True if added, False if budget exhausted.
        """
        if not content or not content.strip():
            return True
        block = f"\n=== {header} ===\n{content.strip()}\n"
        if self._char_count + len(block) > self._char_budget:
            logger.debug("Context budget exhausted, skipping section: %s", header)
            return False
        self._sections.append(block)
        self._char_count += len(block)
        return True

    def build(self) -> str:
        """Return the assembled context string."""
        return "".join(self._sections)


def build_agent_context(
    db: Session,
    agent: AgentDefinition,
    user_input: str,
    session_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    organization_id: Optional[uuid.UUID] = None,
    tool_results: Optional[List[Dict[str, Any]]] = None,
    workflow_state: Optional[Dict[str, Any]] = None,
    knowledge_chunks: Optional[List[str]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
    token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET,
) -> str:
    """
    Assemble a fully merged context string for the agent's LLM call.

    This is the SINGLE authoritative function for context assembly.
    It reuses MemoryManager for memory retrieval — no direct DB access.
    """
    ctx = ContextBuilder(token_budget=token_budget)

    # 1. System Prompt (highest priority — always included)
    system_prompt_parts = []
    if agent.system_prompt:
        system_prompt_parts.append(agent.system_prompt)

    # Load from Prompt Platform if a template is configured
    if agent.prompt_template_name:
        try:
            from api.services.prompt import PromptService
            # Attempt to load the prompt template by name for this org
            from api.models.prompt import Prompt
            from sqlalchemy import select
            prompt_obj = db.scalars(
                select(Prompt).where(
                    Prompt.name == agent.prompt_template_name,
                    Prompt.organization_id == (organization_id or agent.organization_id),
                    Prompt.deleted_at.is_(None),
                )
            ).first()
            if prompt_obj and prompt_obj.content:
                system_prompt_parts.append(f"\n[Agent Prompt Template: {agent.prompt_template_name}]\n{prompt_obj.content}")
        except Exception as e:
            logger.warning("Failed to load prompt template '%s': %s", agent.prompt_template_name, e)

    if system_prompt_parts:
        ctx._add_section("System Instructions", "\n".join(system_prompt_parts))

    # 2. Agent Identity
    identity = (
        f"Agent Name: {agent.name}\n"
        f"Agent Type: {agent.agent_type.value}\n"
        f"Reasoning Mode: {agent.reasoning_mode or 'standard'}\n"
        f"Execution Mode: {agent.execution_mode or 'sequential'}"
    )
    if agent.description:
        identity += f"\nDescription: {agent.description}"
    ctx._add_section("Agent Identity", identity)

    # 3. Organization Memory (brand voice, company facts, guidelines)
    org_id = organization_id or agent.organization_id
    if org_id:
        org_memory = MemoryManager.get_org_memory(db=db, organization_id=org_id)
        if org_memory:
            org_lines = []
            for item in org_memory:
                org_lines.append(f"[{item.category}] {item.key}: {item.value}")
            ctx._add_section("Organization Context & Brand Voice", "\n".join(org_lines))

    # 4. User Profile
    if user_profile:
        profile_lines = [f"{k}: {v}" for k, v in user_profile.items() if v]
        ctx._add_section("User Profile", "\n".join(profile_lines))

    # 5. Long-Term Agent Memory
    if org_id:
        long_term = MemoryManager.read_memory(
            db=db,
            agent_id=agent.id,
            organization_id=org_id,
            memory_type=MemoryType.LONG_TERM,
            limit=10,
        )
        if long_term:
            lt_lines = [f"• {m.memory_key}: {m.memory_value}" for m in long_term]
            ctx._add_section("Agent Long-Term Memory", "\n".join(lt_lines))

    # 6. Conversation History (truncated to last N turns)
    if conversation_history:
        history_lines = []
        for turn in conversation_history[-10:]:
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")[:500]
            history_lines.append(f"{role}: {content}")
        ctx._add_section("Conversation History", "\n".join(history_lines))

    # 7. Session Short-Term Memory
    if session_id and org_id:
        short_term = MemoryManager.read_memory(
            db=db,
            agent_id=agent.id,
            organization_id=org_id,
            session_id=session_id,
            memory_type=MemoryType.SHORT_TERM,
            limit=10,
        )
        if short_term:
            st_lines = [f"• {m.memory_key}: {m.memory_value}" for m in short_term]
            ctx._add_section("Session Memory", "\n".join(st_lines))

    # 8. Knowledge Chunks (RAG results)
    if knowledge_chunks:
        ctx._add_section("Relevant Knowledge", "\n---\n".join(knowledge_chunks[:5]))

    # 9. Tool Results from this run
    if tool_results:
        tr_lines = []
        for tr in tool_results:
            status = "OK" if tr.get("success") else "FAILED"
            output_preview = str(tr.get("output", ""))[:300]
            tr_lines.append(
                f"Tool: {tr.get('tool_name')} [{status}]\n"
                f"  Output: {output_preview}"
            )
        ctx._add_section("Tool Execution Results", "\n".join(tr_lines))

    # 10. Workflow State
    if workflow_state:
        wf_lines = [f"{k}: {v}" for k, v in workflow_state.items()]
        ctx._add_section("Workflow State", "\n".join(wf_lines))

    # 11. Current Task (always last)
    ctx._add_section("Current User Request", user_input)

    return ctx.build()
