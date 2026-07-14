import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from api.models.prompt import Prompt
from api.schemas.ai import PromptCreate, PromptUpdate


class PromptService:
    @staticmethod
    def create_prompt_version(
        db: Session, prompt_in: PromptCreate, organization_id: uuid.UUID
    ) -> Prompt:
        """
        Create the first version (v1) of a prompt.
        If a prompt with this name already exists, raise an exception.
        """
        existing = db.scalars(
            select(Prompt).where(
                and_(
                    Prompt.name == prompt_in.name,
                    Prompt.organization_id == organization_id,
                )
            )
        ).first()
        if existing:
            raise ValueError(
                "Prompt template with this name already exists in your library. Use the update endpoint to create a new version."
            )

        prompt = Prompt(
            name=prompt_in.name,
            content=prompt_in.content,
            version=1,
            category=prompt_in.category,
            tags=prompt_in.tags,
            is_shared=prompt_in.is_shared if prompt_in.is_shared is not None else True,
            organization_id=organization_id,
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return prompt

    @staticmethod
    def update_prompt_version(
        db: Session, name: str, prompt_in: PromptUpdate, organization_id: uuid.UUID
    ) -> Prompt:
        """
        Increment the prompt version and insert a new historical database record.
        """
        latest = db.scalars(
            select(Prompt)
            .where(
                and_(
                    Prompt.name == name,
                    Prompt.organization_id == organization_id,
                )
            )
            .order_by(Prompt.version.desc())
        ).first()

        if not latest:
            raise ValueError(f"Prompt template named '{name}' not found.")

        # Determine properties falling back to latest version
        new_content = prompt_in.content if prompt_in.content is not None else latest.content
        new_category = prompt_in.category if prompt_in.category is not None else latest.category
        new_tags = prompt_in.tags if prompt_in.tags is not None else latest.tags
        new_is_shared = prompt_in.is_shared if prompt_in.is_shared is not None else latest.is_shared

        new_prompt = Prompt(
            name=name,
            content=new_content,
            version=latest.version + 1,
            category=new_category,
            tags=new_tags,
            is_shared=new_is_shared,
            organization_id=organization_id,
        )
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        return new_prompt

    @staticmethod
    def get_latest_prompt(
        db: Session, name: str, organization_id: uuid.UUID
    ) -> Optional[Prompt]:
        """
        Retrieve the highest version of a prompt template.
        """
        return db.scalars(
            select(Prompt)
            .where(
                and_(
                    Prompt.name == name,
                    Prompt.organization_id == organization_id,
                )
            )
            .order_by(Prompt.version.desc())
        ).first()

    @staticmethod
    def get_prompt_history(
        db: Session, name: str, organization_id: uuid.UUID
    ) -> List[Prompt]:
        """
        Retrieve all version records of a prompt template.
        """
        return list(
            db.scalars(
                select(Prompt)
                .where(
                    and_(
                        Prompt.name == name,
                        Prompt.organization_id == organization_id,
                    )
                )
                .order_by(Prompt.version.desc())
            ).all()
        )

    @staticmethod
    def list_latest_prompts(
        db: Session, organization_id: uuid.UUID
    ) -> List[Prompt]:
        """
        Return the highest version of each prompt template within an organization.
        """
        subq = (
            select(Prompt.name, func.max(Prompt.version).label("max_version"))
            .where(Prompt.organization_id == organization_id)
            .group_by(Prompt.name)
            .subquery()
        )

        query = select(Prompt).join(
            subq,
            and_(
                Prompt.name == subq.c.name,
                Prompt.version == subq.c.max_version,
                Prompt.organization_id == organization_id,
            ),
        )

        return list(db.scalars(query).all())

    @staticmethod
    def delete_prompt_family(
        db: Session, name: str, organization_id: uuid.UUID
    ) -> None:
        """
        Delete all versions of a prompt family.
        """
        prompts = db.scalars(
            select(Prompt).where(
                and_(
                    Prompt.name == name,
                    Prompt.organization_id == organization_id,
                )
            )
        ).all()

        for p in prompts:
            db.delete(p)
        db.commit()
