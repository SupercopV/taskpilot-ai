from typing import Dict, Any
from .state import AgentState
from .llm import llm_service
from ..database.db import log_task_event

async def understand_goal(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Analyzes the natural-language goal, extracts business intent,
    and identifies the targeted company and expected outcomes.
    """
    goal = state["original_goal"]
    task_id = state["task_id"]

    log_task_event(
        task_id=task_id,
        state="UNDERSTAND",
        action="understand_goal",
        status="info",
        message=f"Analyzing natural-language objective: '{goal}'",
        details={"goal": goal}
    )

    plan_data = await llm_service.understand_and_plan(goal)
    company = plan_data.get("target_company", "Acme Corp")
    objective = plan_data.get("objective", f"Process latest invoice from {company}")

    log_task_event(
        task_id=task_id,
        state="UNDERSTAND",
        action="understand_goal",
        status="success",
        message=f"Goal understood: Target organization identified as '{company}'",
        details={"target_company": company, "objective": objective}
    )

    return {
        "target_company": company,
        "interpreted_objective": objective,
        "status": "PLANNING"
    }

async def create_plan(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Generates an ordered execution plan of discrete autonomous steps with tools.
    """
    goal = state["original_goal"]
    task_id = state["task_id"]
    company = state.get("target_company") or "Acme Corp"

    plan_data = await llm_service.understand_and_plan(goal)
    plan_steps = plan_data.get("plan", [])

    log_task_event(
        task_id=task_id,
        state="PLAN",
        action="create_plan",
        status="success",
        message=f"Autonomous plan formulated ({len(plan_steps)} executable steps)",
        details={"steps": plan_steps}
    )

    return {
        "plan": plan_steps,
        "current_step_index": 0,
        "status": "EXECUTING"
    }
