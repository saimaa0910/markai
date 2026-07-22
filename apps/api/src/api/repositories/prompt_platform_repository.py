"""
EAIMOS Prompt Platform Repository Module — Sprint 4
===================================================
Repository implementations for Prompt Platform models:
Prompt, PromptCollection, PromptFolder, PromptTestCase, PromptEvaluation, PromptExecution, PromptABTest.
"""

from typing import Any, List, Optional
import uuid

from api.models.prompt import (
    Prompt,
    PromptCollection,
    PromptFolder,
    PromptTestCase,
    PromptEvaluation,
    PromptExecution,
)
from api.models.prompt_abtests import PromptABTest
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class EnterprisePromptRepository(TenantRepository[Prompt]):
    """Data access layer for Prompts within an organization."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Prompt, organization_id=organization_id)

    async def get_by_slug(self, session: Any, slug: str) -> Optional[Prompt]:
        filters = [FilterParam(field="slug", operator=FilterOperator.EQ, value=slug)]
        return await self.find_one(session=session, filters=filters)


class EnterprisePromptCollectionRepository(TenantRepository[PromptCollection]):
    """Data access layer for Prompt Collections."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(PromptCollection, organization_id=organization_id)


class EnterprisePromptFolderRepository(TenantRepository[PromptFolder]):
    """Data access layer for Prompt Folders."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(PromptFolder, organization_id=organization_id)


class PromptTestCaseRepository(TenantRepository[PromptTestCase]):
    """Data access layer for Prompt Test Cases."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(PromptTestCase, organization_id=organization_id)


class PromptEvaluationRepository(TenantRepository[PromptEvaluation]):
    """Data access layer for Prompt Evaluation Results."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(PromptEvaluation, organization_id=organization_id)


class PromptABTestRepository(TenantRepository[PromptABTest]):
    """Data access layer for Prompt A/B Experiments."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(PromptABTest, organization_id=organization_id)
