from typing import Dict, Any, List
from api.ai.capabilities.workflow.helpers import has_cyclic_dependency

def reflect_on_workflow(
    steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Check workflow steps for cycle safety and trigger dependencies."""
    warnings = []
    
    # 1. Validate DAG cycles
    cycles = has_cyclic_dependency(steps)
    if cycles:
        warnings.append("Cyclic dependency error: Infinite loop detected in execution graph. Steps must form a Directed Acyclic Graph (DAG).")
        
    # 2. Check orphan dependencies (referencing non-existent steps)
    step_ids = {s.get("step_id") for s in steps}
    for s in steps:
        for dep in s.get("depends_on", []):
            if dep not in step_ids:
                warnings.append(f"Missing dependency error: Step '{s.get('step_id')}' depends on '{dep}', which is not defined in the workflow.")
                
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "critique": "\n".join(warnings) if warnings else "Workflow graph is cycle-safe and valid."
    }
