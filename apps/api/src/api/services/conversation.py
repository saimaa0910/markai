import uuid
import time
from typing import List, Optional, Generator, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from api.models.conversation import Conversation
from api.models.message import Message
from api.models.ai_platform import AIModel
from api.models.chat_participant import ChatParticipant
from api.models.file_asset import FileAsset
from api.models.chat_attachment import ChatAttachment
from api.ai.gateway.coordinator import AIGateway
from api.repositories.conversation import conversation_repo, message_repo


class ConversationService:
    @staticmethod
    def create_conversation(
        db: Session,
        title: str,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> Conversation:
        """Create a new conversation thread."""
        conv = Conversation(
            title=title,
            user_id=user_id,
            organization_id=organization_id,
            temperature=temperature,
            system_prompt=system_prompt,
            model_name=model_name or "openai/gpt-oss-120b",
            provider_name=provider_name or "groq",
            is_archived=False,
            is_favorite=False,
            is_pinned=False,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        # Add creator as owner participant
        owner_participant = ChatParticipant(
            conversation_id=conv.id,
            user_id=user_id,
            role="owner"
        )
        db.add(owner_participant)
        db.commit()

        return conv

    @staticmethod
    def post_message(
        db: Session,
        conversation_id: uuid.UUID,
        content: str,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        model_name: str,
        prompt_id: Optional[uuid.UUID] = None,
        system_prompt: Optional[str] = None,
        rag_enabled: bool = False,
        attachment_ids: Optional[List[uuid.UUID]] = None,
        **kwargs: Any,
    ) -> Message:
        """Submit a user prompt, run gateway completion, and record assistant response."""
        # 1. Log user message
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            model_used=model_name or "openai/gpt-oss-120b",
        )
        db.add(user_msg)
        db.commit()

        # Link attachments
        if attachment_ids:
            for fa_id in attachment_ids:
                file_asset = db.query(FileAsset).filter(FileAsset.id == fa_id).first()
                if file_asset:
                    attachment = ChatAttachment(
                        message_id=user_msg.id,
                        filename=file_asset.filename,
                        file_type=file_asset.file_type,
                        file_size=file_asset.file_size,
                        storage_url=file_asset.storage_url
                    )
                    db.add(attachment)
            db.commit()

        # 2. Compile system instruction override
        system_instruction = system_prompt
        if prompt_id:
            from api.models.prompt import Prompt
            p_tmpl = db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.organization_id == organization_id).first()
            if p_tmpl:
                system_instruction = p_tmpl.content

        # 3. Retrieve chronological thread history
        history = message_repo.get_by_conversation_id(db, conversation_id)
        messages_payload = []
        if system_instruction:
            messages_payload.append({"role": "system", "content": system_instruction})
        for h in history:
            messages_payload.append({"role": h.role, "content": h.content})

        # 4. Trigger AIGateway
        gateway = AIGateway()
        res = gateway.chat(
            db=db,
            messages=messages_payload,
            organization_id=organization_id,
            user_id=user_id,
            rag_enabled=rag_enabled,
            model_name=model_name or "openai/gpt-oss-120b",
            **kwargs,
        )

        # 5. Log assistant response with full telemetry metrics
        p_tokens = res.get("prompt_tokens") or 0
        c_tokens = res.get("completion_tokens") or 0
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=res["content"],
            model_used=res.get("model", model_name),
            provider_used=res.get("provider"),
            latency_ms=res.get("latency_ms"),
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=p_tokens + c_tokens,
            cost_usd=res.get("cost_usd"),
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return assistant_msg

    @staticmethod
    def stream_response(
        db: Session,
        conversation_id: uuid.UUID,
        content: str,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        model_name: str,
        prompt_id: Optional[uuid.UUID] = None,
        system_prompt: Optional[str] = None,
        rag_enabled: bool = False,
        attachment_ids: Optional[List[uuid.UUID]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Submit a user prompt and stream back Server-Sent Events (SSE) data chunks, logging metrics upon completion."""
        # 1. Log user message
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            model_used=model_name or "openai/gpt-oss-120b",
        )
        db.add(user_msg)
        db.commit()

        # Link attachments
        if attachment_ids:
            for fa_id in attachment_ids:
                file_asset = db.query(FileAsset).filter(FileAsset.id == fa_id).first()
                if file_asset:
                    attachment = ChatAttachment(
                        message_id=user_msg.id,
                        filename=file_asset.filename,
                        file_type=file_asset.file_type,
                        file_size=file_asset.file_size,
                        storage_url=file_asset.storage_url
                    )
                    db.add(attachment)
            db.commit()

        # 2. Compile system instruction override
        system_instruction = system_prompt
        if prompt_id:
            from api.models.prompt import Prompt
            p_tmpl = db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.organization_id == organization_id).first()
            if p_tmpl:
                system_instruction = p_tmpl.content

        # 3. Retrieve chronological history
        history = message_repo.get_by_conversation_id(db, conversation_id)
        messages_payload = []
        if system_instruction:
            messages_payload.append({"role": "system", "content": system_instruction})
        for h in history:
            messages_payload.append({"role": h.role, "content": h.content})

        # 4. Initialize stream coordinator
        gateway = AIGateway()
        start_time = time.perf_counter()
        content_accum = []
        provider_used = "groq"
        model_used = model_name or "openai/gpt-oss-120b"

        try:
            generator = gateway.stream(
                db=db,
                messages=messages_payload,
                organization_id=organization_id,
                user_id=user_id,
                rag_enabled=rag_enabled,
                model_name=model_used,
                **kwargs,
            )

            for chunk in generator:
                if "content" in chunk:
                    content_accum.append(chunk["content"])
                if "provider" in chunk:
                    provider_used = chunk["provider"]
                if "model" not in chunk and model_used:
                    chunk["model"] = model_used
                if "provider" not in chunk:
                    chunk["provider"] = provider_used
                import json
                yield f"data: {json.dumps(chunk)}\n\n"

            # 5. Calculate final tokens & cost
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            full_content = "".join(content_accum)
            prompt_tokens = len(content.split())
            completion_tokens = len(full_content.split())
            total_tokens = prompt_tokens + completion_tokens

            # Lookup model for price calc
            model_meta = db.query(AIModel).filter(AIModel.model_name == model_used, AIModel.is_active == True).first()
            cost_usd = Decimal("0.0")
            if model_meta:
                cost_usd = (Decimal(prompt_tokens) * Decimal(model_meta.input_token_price) + Decimal(completion_tokens) * Decimal(model_meta.output_token_price)) / Decimal("1000000")

            # 6. Save assistant message log
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_content,
                model_used=model_used,
                provider_used=provider_used,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=float(cost_usd),
            )
            db.add(assistant_msg)
            db.commit()

        except Exception as e:
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            db.rollback()
