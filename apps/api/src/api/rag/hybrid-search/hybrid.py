"""
Dense + Sparse Hybrid Search.
"""

from typing import List, Dict, Any


class HybridSearchEngine:
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # TODO: Execute BM25 + Vector Search fusion
        return []


hybrid_search_engine = HybridSearchEngine()
