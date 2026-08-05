"""
Knowledge Controller.
"""

from typing import List, Dict, Any


class KnowledgeController:
    async def list_documents(self) -> List[Dict[str, Any]]:
        return []


knowledge_controller = KnowledgeController()
