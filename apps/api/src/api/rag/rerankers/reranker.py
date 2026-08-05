"""
Cross-Encoder Reranker.
"""

from typing import List, Dict, Any


class CrossEncoderReranker:
    async def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # TODO: Compute relevance score and sort documents
        return documents


cross_encoder_reranker = CrossEncoderReranker()
