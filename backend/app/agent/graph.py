import json
from datetime import datetime
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from .state import AgentState
from .planner import understand_goal, create_plan
from .executor import select_tool, execute_action
from .recovery import detect_failure, recover
from .verifier import verify_result
from .llm import llm_service
from ..database.db import log_task_event, get_db_connection

async def complete_task(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Compiles the final evidence bundle, generates the executive summary,
    and marks the task as completed.
    """
    task_id = state["task_id"]
    goal = state["original_goal"]
    inv_data = state.get("invoice_data") or {}
    finance_rec = state.get("finance_record") or {}
    verification = state.get("verification_data") or {}
    evidence = state.get("evidence_bundle") or {}
    recovery_occurred = (state.get("retry_count", 0) > 0)

    summary = await llm_service.generate_completion_summary(
        goal=goal,
        invoice=inv_data,
        finance_record=finance_rec,
        verification=verification,
        recovery_occurred=recovery_occurred
    )

    evidence["final_summary"] = summary
    evidence["completed_at"] = datetime.utcnow().isoformat() + "Z"

    log_task_event(
        task_id=task_id,
        state="COMPLETE",
        action="complete_task",
        status="success",
        message="[COMPLETED] Task completed successfully. All ledger records verified.",
        details={
            "invoice": inv_data,
            "finance_record": finance_rec,
            "verification": verification,
            "summary": summary
        }
    )

    # Persist final result to SQLite
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat() + "Z"
        result_payload = json.dumps({
            "task_id": task_id,
            "status": "COMPLETED",
            "invoice": inv_data,
            "finance_record": finance_rec,
            "verification": verification,
            "evidence": evidence,
            "summary": summary
        })
        cursor.execute("""
        UPDATE tasks 
        SET status = 'COMPLETED', result_json = ?, updated_at = ?
        WHERE task_id = ?;
        """, (result_payload, now, task_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error persisting completed task: {e}")

    return {
        "status": "COMPLETED",
        "final_summary": summary,
        "evidence_bundle": evidence
    }

def route_after_execution(state: AgentState) -> Literal["detect_failure", "verify_result", "select_tool", "complete_task", "__end__"]:
    """
    Conditional edge router evaluating state after tool execution.
    """
    status = state.get("status")

    if status == "WAITING_FOR_APPROVAL" or status == "REJECTED":
        return "__end__"

    if status == "DETECT_FAILURE":
        return "detect_failure"

    if status == "VERIFYING":
        return "verify_result"

    plan = state.get("plan", [])
    step_idx = state.get("current_step_index", 0)
    
    if step_idx >= len(plan):
        return "verify_result" if not state.get("verification_data") else "complete_task"

    return "select_tool"

def route_after_failure_detection(state: AgentState) -> Literal["recover", "__end__"]:
    """
    Routes to recover node if recoverable within retry budget, otherwise ends as failed.
    """
    if state.get("is_recoverable", False):
        return "recover"
    return "__end__"

def route_after_verification(state: AgentState) -> Literal["complete_task", "__end__"]:
    """
    Routes to completion if verified, else terminates as failed.
    """
    status = state.get("status")
    if status == "COMPLETED":
        return "complete_task"
    return "__end__"

def build_agent_graph() -> StateGraph:
    """
    Assembles the explicit LangGraph state machine.
    """
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("understand_goal", understand_goal)
    workflow.add_node("create_plan", create_plan)
    workflow.add_node("select_tool", select_tool)
    workflow.add_node("execute_action", execute_action)
    workflow.add_node("detect_failure", detect_failure)
    workflow.add_node("recover", recover)
    workflow.add_node("verify_result", verify_result)
    workflow.add_node("complete_task", complete_task)

    # Set Entry Point
    workflow.set_entry_point("understand_goal")

    # Transitions
    workflow.add_edge("understand_goal", "create_plan")
    workflow.add_edge("create_plan", "select_tool")
    workflow.add_edge("select_tool", "execute_action")

    # Conditional Edges from Execution
    workflow.add_conditional_edges(
        "execute_action",
        route_after_execution,
        {
            "select_tool": "select_tool",
            "detect_failure": "detect_failure",
            "verify_result": "verify_result",
            "complete_task": "complete_task",
            "__end__": END
        }
    )

    # Conditional Edges from Failure Detection
    workflow.add_conditional_edges(
        "detect_failure",
        route_after_failure_detection,
        {
            "recover": "recover",
            "__end__": END
        }
    )

    # Transition from Recovery back to Execution (Retry Step)
    workflow.add_edge("recover", "execute_action")

    # Conditional Edges from Verification
    workflow.add_conditional_edges(
        "verify_result",
        route_after_verification,
        {
            "complete_task": "complete_task",
            "__end__": END
        }
    )

    workflow.add_edge("complete_task", END)

    return workflow.compile()

# Precompiled graph instance
agent_app = build_agent_graph()
