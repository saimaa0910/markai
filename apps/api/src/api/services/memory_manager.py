"""
Agent Memory Manager
====================
Provides read/write/summarize operations for all memory types.
Used by the AgentExecutor to maintain agent context across runs.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from api.models.memory import AgentMemory, ConversationMemory, OrganizationMemory, MemoryType
from api.models.agent import AgentSession


class MemoryManager:
    """
    Central memory management service for the AI Agent Platform.
    Implements a three-tier memory architecture:
    - Short-term: Session-scoped, reset after session ends
    - Long-term: Agent-scoped, persists across sessions
    - Organizational: Shared across all agents in the org
    """

    @staticmethod
    def write_memory(
        db: Session,
        agent_id: uuid.UUID,
        organization_id: uuid.UUID,
        key: str,
        value: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        session_id: Optional[uuid.UUID] = None,
        importance: float = 0.5,
    ) -> AgentMemory:
        """
        Write or update a memory item.
        If key already exists, update in place.
        """
        stmt = select(AgentMemory).where(
            and_(
                AgentMemory.agent_id == agent_id,
                AgentMemory.memory_key == key,
                AgentMemory.organization_id == organization_id,
                AgentMemory.deleted_at.is_(None),
                AgentMemory.session_id == session_id if session_id else AgentMemory.session_id.is_(None),
            )
        )
        existing = db.scalars(stmt).first()

        if existing:
            existing.memory_value = value
            existing.importance = importance
            existing.access_count += 1
            db.commit()
            db.refresh(existing)
            return existing

        memory = AgentMemory(
            agent_id=agent_id,
            session_id=session_id,
            organization_id=organization_id,
            memory_type=memory_type,
            memory_key=key,
            memory_value=value,
            importance=importance,
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    @staticmethod
    def read_memory(
        db: Session,
        agent_id: uuid.UUID,
        organization_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 20,
    ) -> List[AgentMemory]:
        """
        Retrieve memory items for an agent, ordered by importance descending.
        """
        filters = [
            AgentMemory.agent_id == agent_id,
            AgentMemory.organization_id == organization_id,
            AgentMemory.deleted_at.is_(None),
        ]
        if session_id:
            filters.append(AgentMemory.session_id == session_id)
        if memory_type:
            filters.append(AgentMemory.memory_type == memory_type)

        return list(
            db.scalars(
                select(AgentMemory)
                .where(and_(*filters))
                .order_by(AgentMemory.importance.desc())
                .limit(limit)
            ).all()
        )

    @staticmethod
    def build_memory_context(
        db: Session,
        agent_id: uuid.UUID,
        organization_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
        max_items: int = 20,
    ) -> str:
        """
        Build a formatted memory context string for injection into prompts.
        Combines long-term agent memory and current session memory.
        """
        long_term = MemoryManager.read_memory(
            db=db,
            agent_id=agent_id,
            organization_id=organization_id,
            memory_type=MemoryType.LONG_TERM,
            limit=max_items // 2,
        )
        short_term: List[AgentMemory] = []
        if session_id:
            short_term = MemoryManager.read_memory(
                db=db,
                agent_id=agent_id,
                organization_id=organization_id,
                session_id=session_id,
                memory_type=MemoryType.SHORT_TERM,
                limit=max_items // 2,
            )

        org_memory = MemoryManager.get_org_memory(
            db=db, organization_id=organization_id
        )

        lines = []
        if org_memory:
            lines.append("=== Organization Context ===")
            for item in org_memory:
                lines.append(f"[{item.category}] {item.key}: {item.value}")

        if long_term:
            lines.append("\n=== Agent Long-Term Memory ===")
            for m in long_term:
                lines.append(f"• {m.memory_key}: {m.memory_value}")

        if short_term:
            lines.append("\n=== Current Session Context ===")
            for m in short_term:
                lines.append(f"• {m.memory_key}: {m.memory_value}")

        return "\n".join(lines)

    @staticmethod
    def get_org_memory(
        db: Session,
        organization_id: uuid.UUID,
        category: Optional[str] = None,
    ) -> List[OrganizationMemory]:
        """Retrieve active organizational memory items."""
        filters = [
            OrganizationMemory.organization_id == organization_id,
            OrganizationMemory.is_active == True,
            OrganizationMemory.deleted_at.is_(None),
        ]
        if category:
            filters.append(OrganizationMemory.category == category)

        return list(
            db.scalars(
                select(OrganizationMemory).where(and_(*filters))
            ).all()
        )

    @staticmethod
    def write_org_memory(
        db: Session,
        organization_id: uuid.UUID,
        category: str,
        key: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrganizationMemory:
        """Write or update an organizational memory entry."""
        existing = db.scalars(
            select(OrganizationMemory).where(
                and_(
                    OrganizationMemory.organization_id == organization_id,
                    OrganizationMemory.category == category,
                    OrganizationMemory.key == key,
                    OrganizationMemory.deleted_at.is_(None),
                )
            )
        ).first()

        if existing:
            existing.value = value
            if metadata:
                existing.meta_data = metadata
            db.commit()
            db.refresh(existing)
            return existing

        entry = OrganizationMemory(
            organization_id=organization_id,
            category=category,
            key=key,
            value=value,
            meta_data=metadata,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def save_conversation_summary(
        db: Session,
        session_id: uuid.UUID,
        organization_id: uuid.UUID,
        summary: str,
        turns_covered: int,
        turn_index: int,
    ) -> ConversationMemory:
        """Persist an LLM-generated conversation summary."""
        cm = ConversationMemory(
            session_id=session_id,
            organization_id=organization_id,
            summary=summary,
            turns_covered=turns_covered,
            summary_turn_index=turn_index,
        )
        db.add(cm)
        db.commit()
        db.refresh(cm)
        return cm

    @staticmethod
    def get_latest_summary(
        db: Session,
        session_id: uuid.UUID,
    ) -> Optional[ConversationMemory]:
        """Retrieve the most recent conversation summary for a session."""
        return db.scalars(
            select(ConversationMemory)
            .where(ConversationMemory.session_id == session_id)
            .order_by(ConversationMemory.summary_turn_index.desc())
        ).first()

    @staticmethod
    def clear_session_memory(
        db: Session,
        session_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> int:
        """Soft-delete all short-term memory for a completed session."""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        items = list(
            db.scalars(
                select(AgentMemory).where(
                    and_(
                        AgentMemory.session_id == session_id,
                        AgentMemory.memory_type == MemoryType.SHORT_TERM,
                        AgentMemory.deleted_at.is_(None),
                    )
                )
            ).all()
        )
        for item in items:
            item.deleted_at = now
        db.commit()
        return len(items)
