"""
Knowledge Service.
"""

from typing import List, Dict, Any


class KnowledgeService:
    async def get_docs(self) -> List[Dict[str, Any]]:
        return []


knowledge_service = KnowledgeService()
