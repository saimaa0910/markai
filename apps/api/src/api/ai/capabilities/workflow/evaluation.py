from typing import Dict, Any, List
from api.ai.capabilities.workflow.helpers import has_cyclic_dependency

def evaluate_workflow(
    steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Grade workflow complexity and correctness."""
    # 1. Cycle safety score (Max 50 points)
    cycles = has_cyclic_dependency(steps)
    cycle_score = 0.0 if cycles else 50.0
    
    # 2. Step connectivity (Max 20 points)
    # Check if there are unlinked orphaned steps (not triggers and not depending on anything)
    step_ids = {s.get("step_id") for s in steps}
    connected_count = 0
    for s in steps:
        has_incoming = len(s.get("depends_on", [])) > 0
        has_outgoing = any(s.get("step_id") in other.get("depends_on", []) for other in steps)
        if has_incoming or has_outgoing or len(steps) == 1:
            connected_count += 1
            
    connect_score = (connected_count / len(steps) * 20.0) if steps else 20.0
    
    # 3. Efficiency / Parallel potential (Max 30 points)
    # Heuristic: if steps count > 2 and we have multiple start nodes (in-degree = 0), we have parallel paths!
    in_degrees = {s.get("step_id"): 0 for s in steps}
    for s in steps:
        for dep in s.get("depends_on", []):
            if s.get("step_id") in in_degrees:
                in_degrees[s.get("step_id")] += 1
                
    start_nodes = sum(1 for v in in_degrees.values() if v == 0)
    efficiency_score = 30.0 if start_nodes > 1 else 15.0
    if len(steps) <= 1:
        efficiency_score = 30.0
        
    total_score = cycle_score + connect_score + efficiency_score
    
    return {
        "score": round(total_score, 1),
        "metrics": {
            "cycle_safety_index": round(cycle_score / 50.0 * 100.0, 1),
            "graph_connectivity": round(connect_score / 20.0 * 100.0, 1) if connect_score > 0 else 0.0,
            "parallel_efficiency": round(efficiency_score / 30.0 * 100.0, 1) if efficiency_score > 0 else 0.0
        }
    }
