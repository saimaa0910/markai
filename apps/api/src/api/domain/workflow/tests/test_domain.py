"""
Workflow Domain Unit Tests.
"""

from api.domain.workflow.validator import validate_dag_nodes


def test_dag_validation():
    assert validate_dag_nodes([{"id": "n1"}]) is True
    assert validate_dag_nodes([]) is False
