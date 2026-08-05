"""
Workflow Validators.
"""

from typing import List


def validate_dag_nodes(nodes: List[dict]) -> bool:
    return len(nodes) > 0
