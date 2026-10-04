from typing import Dict, Any
from .state import AgentState
from ..database.db import log_task_event

async def detect_failure(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Analyzes the last tool execution result to detect failures,
    evaluates failure classification (transient vs fatal), and decides whether recovery is feasible.
    """
    last_res = state.get("last_tool_result") or {}
    task_id = state["task_id"]
    error = last_res.get("error") or "Unknown tool execution failure"
    tool_name = state.get("current_tool", "unknown_tool")

    log_task_event(
        task_id=task_id,
        state="DETECT_FAILURE",
        action="detect_failure",
        tool=tool_name,
        status="error",
        message=f"ERROR: {error}",
        details={"tool": tool_name, "result": last_res}
    )

    # Check retry budget
    retries = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    is_recoverable = last_res.get("recoverable", True) and (retries < max_retries)

    return {
        "error_message": error,
        "is_recoverable": is_recoverable,
        "status": "RECOVERING" if is_recoverable else "FAILED"
    }

async def recover(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Formulates and executes an autonomous recovery strategy.
    For validation/network errors, resets failure flags, logs recovery strategy,
    increments retry counter, and resumes execution.
    """
    task_id = state["task_id"]
    tool_name = state.get("current_tool", "submit_invoice")
    retries = state.get("retry_count", 0) + 1
    max_retries = state.get("max_retries", 3)
    
    strategy = f"Retry {tool_name} with cleared validation state (Attempt {retries} of {max_retries})"

    log_task_event(
        task_id=task_id,
        state="RECOVER",
        action="recover",
        tool=tool_name,
        status="warning",
        message=f"Recovery strategy: {strategy}",
        details={
            "recovery_strategy": strategy,
            "retry_count": retries,
            "max_retries": max_retries
        }
    )

    # Disable failure simulation so the retried attempt succeeds
    return {
        "retry_count": retries,
        "simulate_failure": False,
        "recovery_strategy": strategy,
        "error_message": None,
        "status": "EXECUTING"
    }
