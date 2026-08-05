"""
Semantic & Fixed-size Chunker.
"""

from typing import List


class TextChunker:
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        # TODO: Split text into semantic chunks
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


text_chunker = TextChunker()
