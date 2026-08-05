from typing import Dict, List, Any
from api.ai.capabilities import BaseCapability

def has_cyclic_dependency(steps: List[Dict[str, Any]]) -> bool:
    """
    Check if the workflow steps contain a cyclic dependency (infinite loop)
    using Kahn's Topological Sorting Algorithm.
    Returns True if cycles exist (invalid DAG), False otherwise.
    """
    # 1. Build adjacency list and in-degree map
    adj = {}
    in_degree = {}
    
    # Initialize entries
    for step in steps:
        step_id = step.get("step_id")
        if step_id:
            adj[step_id] = []
            in_degree[step_id] = 0
            
    # Populate dependencies
    for step in steps:
        step_id = step.get("step_id")
        depends_on = step.get("depends_on", [])
        for dep in depends_on:
            if dep in adj and step_id in adj:
                adj[dep].append(step_id)
                in_degree[step_id] += 1
                
    # 2. Find nodes with in-degree 0 (start nodes)
    queue = [node for node, deg in in_degree.items() if deg == 0]
    visited_count = 0
    
    # 3. Process queue
    while queue:
        curr = queue.pop(0)
        visited_count += 1
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    # If visited nodes do not equal total nodes, a cycle exists!
    return visited_count != len(adj) if adj else False

WORKFLOW_CAPABILITY = BaseCapability(
    name="WORKFLOW",
    description="Enterprise Automation Builder, event trigger logic, and DAG cycle validator capability.",
    input_schema={
        "type": "object",
        "properties": {
            "workflow_name": {"type": "string"},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_id": {"type": "string"},
                        "action_type": {"type": "string"},
                        "depends_on": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["step_id", "action_type"]
                }
            }
        },
        "required": ["workflow_name", "steps"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "cycles_detected": {"type": "boolean"},
            "timeline_length_sec": {"type": "number"}
        }
    },
    estimated_runtime=14,
    estimated_cost=0.016,
    required_tools=["workflow_tool"],
    required_permissions=["manage_workflow"],
    supports_delegation=True,
    supports_parallel_execution=True,
    prompt_template="Standard workflow orchestration directives."
)
