"""
Knowledge Repository.
"""

from typing import List, Any


class KnowledgeRepository:
    async def get_all_documents(self) -> List[Any]:
        return []


knowledge_repository = KnowledgeRepository()
