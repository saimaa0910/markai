import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, desc, asc

from api.models.prompt import (
    Prompt, PromptVersion, PromptFolder, PromptCollection,
    PromptCategory, PromptTag, PromptVariable, PromptShare,
    PromptFavorite, PromptExecution, PromptEvaluation, PromptAnalytics,
    PromptTemplate, PromptAuditLog, PromptComment, PromptTestCase
)


class PromptRepository:
    @staticmethod
    def create(db: Session, prompt: Prompt) -> Prompt:
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return prompt

    @staticmethod
    def get_by_id(db: Session, prompt_id: uuid.UUID, organization_id: uuid.UUID, include_deleted: bool = False) -> Optional[Prompt]:
        stmt = select(Prompt).where(
            Prompt.id == prompt_id,
            Prompt.organization_id == organization_id,
        )
        if not include_deleted:
            stmt = stmt.where(Prompt.deleted_at.is_(None))
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_name(db: Session, name: str, organization_id: uuid.UUID, include_deleted: bool = False) -> Optional[Prompt]:
        stmt = select(Prompt).where(
            Prompt.name == name,
            Prompt.organization_id == organization_id,
        )
        if not include_deleted:
            stmt = stmt.where(Prompt.deleted_at.is_(None))
        return db.scalars(stmt.order_by(Prompt.version.desc())).first()

    @staticmethod
    def list_by_organization(
        db: Session,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_archived: bool = False,
        category: Optional[str] = None,
        folder_id: Optional[uuid.UUID] = None,
        collection_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[Prompt], int]:
        subq = (
            select(Prompt.name, func.max(Prompt.version).label("max_version"))
            .where(Prompt.organization_id == organization_id)
        )
        if not include_archived:
            subq = subq.where(Prompt.is_archived == False, Prompt.deleted_at.is_(None))
        subq = subq.group_by(Prompt.name).subquery()

        stmt = select(Prompt).join(
            subq,
            and_(
                Prompt.name == subq.c.name,
                Prompt.version == subq.c.max_version,
                Prompt.organization_id == organization_id,
            ),
        )

        if not include_archived:
            stmt = stmt.where(Prompt.is_archived == False, Prompt.deleted_at.is_(None))
        if category:
            stmt = stmt.where(Prompt.category == category)
        if folder_id:
            stmt = stmt.where(Prompt.folder_id == folder_id)
        if collection_id:
            stmt = stmt.where(Prompt.collection_id == collection_id)
        if status:
            stmt = stmt.where(Prompt.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Prompt.updated_at.desc()).offset(skip).limit(limit)
        results = list(db.scalars(stmt).all())
        return results, total

    @staticmethod
    def search(
        db: Session,
        organization_id: uuid.UUID,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        folder_id: Optional[uuid.UUID] = None,
        collection_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        owner_id: Optional[uuid.UUID] = None,
        is_archived: bool = False,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Prompt], int]:
        subq = (
            select(Prompt.name, func.max(Prompt.version).label("max_version"))
            .where(Prompt.organization_id == organization_id)
            .group_by(Prompt.name)
            .subquery()
        )

        stmt = select(Prompt).join(
            subq,
            and_(
                Prompt.name == subq.c.name,
                Prompt.version == subq.c.max_version,
                Prompt.organization_id == organization_id,
            ),
        )

        if is_archived:
            stmt = stmt.where(Prompt.is_archived == True)
        else:
            stmt = stmt.where(Prompt.deleted_at.is_(None))

        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Prompt.name.ilike(pattern),
                    Prompt.content.ilike(pattern),
                    Prompt.description.ilike(pattern),
                    Prompt.tags.ilike(pattern),
                )
            )
        if category:
            stmt = stmt.where(Prompt.category == category)
        if tag:
            stmt = stmt.where(Prompt.tags.ilike(f"%{tag}%"))
        if folder_id:
            stmt = stmt.where(Prompt.folder_id == folder_id)
        if collection_id:
            stmt = stmt.where(Prompt.collection_id == collection_id)
        if status:
            stmt = stmt.where(Prompt.status == status)
        if owner_id:
            stmt = stmt.where(Prompt.owner_id == owner_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        sort_col = getattr(Prompt, sort_by, Prompt.updated_at)
        if sort_order.lower() == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(asc(sort_col))

        stmt = stmt.offset(skip).limit(limit)
        results = list(db.scalars(stmt).all())
        return results, total

    @staticmethod
    def soft_delete(db: Session, prompt_name: str, organization_id: uuid.UUID) -> int:
        prompts = list(
            db.scalars(
                select(Prompt).where(
                    Prompt.name == prompt_name,
                    Prompt.organization_id == organization_id,
                    Prompt.deleted_at.is_(None)
                )
            ).all()
        )
        now = datetime.utcnow()
        for p in prompts:
            p.deleted_at = now
            p.is_archived = True
        db.commit()
        return len(prompts)

    @staticmethod
    def restore(db: Session, prompt_name: str, organization_id: uuid.UUID) -> Optional[Prompt]:
        prompts = list(
            db.scalars(
                select(Prompt).where(
                    Prompt.name == prompt_name,
                    Prompt.organization_id == organization_id,
                )
            ).all()
        )
        for p in prompts:
            p.deleted_at = None
            p.is_archived = False
        db.commit()
        return PromptRepository.get_by_name(db, prompt_name, organization_id)

    @staticmethod
    def purge(db: Session, prompt_name: str, organization_id: uuid.UUID) -> int:
        prompts = list(
            db.scalars(
                select(Prompt).where(
                    Prompt.name == prompt_name,
                    Prompt.organization_id == organization_id,
                )
            ).all()
        )
        count = len(prompts)
        for p in prompts:
            db.delete(p)
        db.commit()
        return count


class PromptVersionRepository:
    @staticmethod
    def create(db: Session, version: PromptVersion) -> PromptVersion:
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def get_by_prompt_and_number(
        db: Session, prompt_id: uuid.UUID, version_number: int
    ) -> Optional[PromptVersion]:
        return db.scalars(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.version_number == version_number,
            )
        ).first()

    @staticmethod
    def list_by_prompt(
        db: Session, prompt_id: uuid.UUID
    ) -> List[PromptVersion]:
        return list(
            db.scalars(
                select(PromptVersion)
                .where(PromptVersion.prompt_id == prompt_id)
                .order_by(desc(PromptVersion.version_number))
            ).all()
        )


class FolderRepository:
    @staticmethod
    def create(db: Session, folder: PromptFolder) -> PromptFolder:
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def list_by_org(
        db: Session, organization_id: uuid.UUID, collection_id: Optional[uuid.UUID] = None
    ) -> List[PromptFolder]:
        stmt = select(PromptFolder).where(
            PromptFolder.organization_id == organization_id,
            PromptFolder.deleted_at.is_(None)
        )
        if collection_id:
            stmt = stmt.where(PromptFolder.collection_id == collection_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, folder_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[PromptFolder]:
        return db.scalars(
            select(PromptFolder).where(
                PromptFolder.id == folder_id,
                PromptFolder.organization_id == organization_id,
                PromptFolder.deleted_at.is_(None)
            )
        ).first()


class CollectionRepository:
    @staticmethod
    def create(db: Session, collection: PromptCollection) -> PromptCollection:
        db.add(collection)
        db.commit()
        db.refresh(collection)
        return collection

    @staticmethod
    def list_by_org(db: Session, organization_id: uuid.UUID) -> List[PromptCollection]:
        return list(
            db.scalars(
                select(PromptCollection).where(
                    PromptCollection.organization_id == organization_id,
                    PromptCollection.is_archived == False,
                    PromptCollection.deleted_at.is_(None)
                )
            ).all()
        )

    @staticmethod
    def get_by_id(db: Session, collection_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[PromptCollection]:
        return db.scalars(
            select(PromptCollection).where(
                PromptCollection.id == collection_id,
                PromptCollection.organization_id == organization_id,
                PromptCollection.deleted_at.is_(None)
            )
        ).first()


class ExecutionRepository:
    @staticmethod
    def create(db: Session, execution: PromptExecution) -> PromptExecution:
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def list_by_prompt(
        db: Session, prompt_id: uuid.UUID, organization_id: uuid.UUID, limit: int = 50
    ) -> List[PromptExecution]:
        return list(
            db.scalars(
                select(PromptExecution)
                .where(
                    PromptExecution.prompt_id == prompt_id,
                    PromptExecution.organization_id == organization_id,
                )
                .order_by(desc(PromptExecution.created_at))
                .limit(limit)
            ).all()
        )


class EvaluationRepository:
    @staticmethod
    def create(db: Session, evaluation: PromptEvaluation) -> PromptEvaluation:
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    @staticmethod
    def list_by_prompt(
        db: Session, prompt_id: uuid.UUID, organization_id: uuid.UUID
    ) -> List[PromptEvaluation]:
        return list(
            db.scalars(
                select(PromptEvaluation)
                .where(
                    PromptEvaluation.prompt_id == prompt_id,
                    PromptEvaluation.organization_id == organization_id,
                )
                .order_by(desc(PromptEvaluation.created_at))
            ).all()
        )


class ShareRepository:
    @staticmethod
    def create(db: Session, share: PromptShare) -> PromptShare:
        db.add(share)
        db.commit()
        db.refresh(share)
        return share

    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[PromptShare]:
        return db.scalars(
            select(PromptShare).where(
                PromptShare.share_token == token,
                PromptShare.deleted_at.is_(None)
            )
        ).first()


class FavoriteRepository:
    @staticmethod
    def add_favorite(db: Session, fav: PromptFavorite) -> PromptFavorite:
        db.add(fav)
        db.commit()
        db.refresh(fav)
        return fav

    @staticmethod
    def remove_favorite(db: Session, prompt_id: uuid.UUID, user_id: uuid.UUID, organization_id: uuid.UUID) -> bool:
        fav = db.scalars(
            select(PromptFavorite).where(
                PromptFavorite.prompt_id == prompt_id,
                PromptFavorite.user_id == user_id,
                PromptFavorite.organization_id == organization_id
            )
        ).first()
        if fav:
            db.delete(fav)
            db.commit()
            return True
        return False

    @staticmethod
    def is_favorite(db: Session, prompt_id: uuid.UUID, user_id: uuid.UUID, organization_id: uuid.UUID) -> bool:
        fav = db.scalars(
            select(PromptFavorite).where(
                PromptFavorite.prompt_id == prompt_id,
                PromptFavorite.user_id == user_id,
                PromptFavorite.organization_id == organization_id
            )
        ).first()
        return fav is not None


class AnalyticsRepository:
    @staticmethod
    def get_or_create(db: Session, prompt_id: uuid.UUID, organization_id: uuid.UUID) -> PromptAnalytics:
        analytics = db.scalars(
            select(PromptAnalytics).where(
                PromptAnalytics.prompt_id == prompt_id,
                PromptAnalytics.organization_id == organization_id
            )
        ).first()
        if not analytics:
            analytics = PromptAnalytics(
                prompt_id=prompt_id,
                organization_id=organization_id,
                total_executions=0,
                total_tokens=0,
                total_cost_usd=0.0,
                avg_latency_ms=0.0,
                success_rate=100.0,
            )
            db.add(analytics)
            db.commit()
            db.refresh(analytics)
        return analytics

    @staticmethod
    def record_execution(
        db: Session,
        prompt_id: uuid.UUID,
        organization_id: uuid.UUID,
        tokens: int,
        cost: float,
        latency: int,
        success: bool = True
    ) -> PromptAnalytics:
        analytics = AnalyticsRepository.get_or_create(db, prompt_id, organization_id)
        
        prev_total = analytics.total_executions
        new_total = prev_total + 1
        analytics.total_executions = new_total
        analytics.total_tokens += tokens
        analytics.total_cost_usd += cost
        
        # Recalculate average latency
        analytics.avg_latency_ms = ((analytics.avg_latency_ms * prev_total) + latency) / new_total
        analytics.last_executed_at = datetime.utcnow()
        
        if not success:
            failed = (100.0 - analytics.success_rate) * prev_total / 100.0 + 1
            analytics.success_rate = ((new_total - failed) / new_total) * 100.0

        db.commit()
        db.refresh(analytics)
        return analytics


class CategoryRepository:
    @staticmethod
    def create(db: Session, category: PromptCategory) -> PromptCategory:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def list_by_org(db: Session, organization_id: uuid.UUID) -> List[PromptCategory]:
        return list(
            db.scalars(
                select(PromptCategory).where(
                    PromptCategory.organization_id == organization_id,
                    PromptCategory.deleted_at.is_(None)
                ).order_by(PromptCategory.name)
            ).all()
        )


class TagRepository:
    @staticmethod
    def create(db: Session, tag: PromptTag) -> PromptTag:
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    def list_by_org(db: Session, organization_id: uuid.UUID) -> List[PromptTag]:
        return list(
            db.scalars(
                select(PromptTag).where(
                    PromptTag.organization_id == organization_id,
                    PromptTag.deleted_at.is_(None)
                ).order_by(PromptTag.name)
            ).all()
        )


class AuditLogRepository:
    @staticmethod
    def log_action(
        db: Session,
        prompt_name: str,
        action: str,
        organization_id: uuid.UUID,
        prompt_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PromptAuditLog:
        log_entry = PromptAuditLog(
            prompt_id=prompt_id,
            prompt_name=prompt_name,
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            metadata_json=metadata_json,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def list_by_org(
        db: Session, organization_id: uuid.UUID, limit: int = 100
    ) -> List[PromptAuditLog]:
        return list(
            db.scalars(
                select(PromptAuditLog)
                .where(PromptAuditLog.organization_id == organization_id)
                .order_by(desc(PromptAuditLog.created_at))
                .limit(limit)
            ).all()
        )
