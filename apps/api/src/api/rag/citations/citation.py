"""
Source Attribution & Citations Formatter.
"""

from typing import List, Dict, Any


class CitationFormatter:
    def format_citations(self, sources: List[Dict[str, Any]]) -> str:
        # TODO: Format source references as markdown footnotes
        return "\n".join([f"[{i+1}] {s.get('title', 'Doc')}" for i, s in enumerate(sources)])


citation_formatter = CitationFormatter()
