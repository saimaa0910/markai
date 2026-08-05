# Workflow Capability Prompts

SYSTEM_PROMPT = """You are a Principal Automation Engineer and Staff Systems Orchestrator.
You design execution trigger blocks, write retry configurations, plan parallel timeline paths, and resolve cycle dependencies.
"""

PLANNER_PROMPT = """Plan automation pipelines:
1. Establish event triggers.
2. Outline execution steps order.
3. Check for dependency deadlock loops.
4. Construct timelines with start delays.
"""

EXECUTION_PROMPT = """Construct a workflow definition for '{workflow_name}'.
Steps list: {steps}.
Expose visual step triggers, dependencies, and retry timeouts.
"""

REFLECTION_PROMPT = """Critique workflow pipeline safety:
- Verify that no cyclic dependencies exist (e.g. step A depending on B, and B depending on A).
- Verify that steps do not depend on non-existent steps.
- Audit retry strategy parameters for validity.
"""

EVALUATION_PROMPT = """Grade workflow pipelines:
- Cycle safety index (100 if no cycles exist).
- Execution efficiency (number of parallel paths).
- Dependency validation completeness.
"""

REWRITE_PROMPT = """Rewrite the workflow schema to eliminate loop cycles:
{critique}
Original workflow schema:
{content}
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "Workflow: Email sending on new lead trigger",
        "output": {
            "name": "Outbound Lead Email",
            "trigger": {"event_source": "CRM", "event_type": "new_lead"},
            "steps": [
                {"step_id": "fetch_profile", "action_type": "fetch_crm"},
                {"step_id": "generate_copy", "action_type": "content_generation", "depends_on": ["fetch_profile"]},
                {"step_id": "send_mail", "action_type": "email_outbound", "depends_on": ["generate_copy"]}
            ],
            "cycles_detected": False
        }
    }
]
