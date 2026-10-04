import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.db import init_db, get_task_events
from app.agent.graph import agent_app
from app.agent.state import AgentState

async def run_scenario_1():
    print("\n=======================================================")
    print("RUNNING SCENARIO 1: Standard Autonomous Invoice Processing")
    print("=======================================================")
    init_db()

    initial_state: AgentState = {
        "task_id": "test-task-sc1",
        "original_goal": "Find the latest invoice from Acme Corp, extract the invoice amount and due date, enter it into the finance system, and verify that it was successfully recorded.",
        "target_company": None,
        "interpreted_objective": None,
        "status": "PENDING",
        "plan": [],
        "current_step_index": 0,
        "step_count": 0,
        "max_steps": 15,
        "discovered_files": [],
        "selected_invoice_file": None,
        "invoice_data": None,
        "finance_record": None,
        "verification_data": None,
        "evidence_bundle": {},
        "current_tool": None,
        "current_tool_args": None,
        "last_tool_result": None,
        "execution_history": [],
        "error_message": None,
        "is_recoverable": True,
        "retry_count": 0,
        "max_retries": 3,
        "simulate_failure": False,
        "recovery_strategy": None,
        "approval_required": False,
        "approval_status": "NONE",
        "approval_details": None,
        "final_summary": None
    }

    final_state = await agent_app.ainvoke(initial_state)
    print("\nFinal Agent Status:", final_state.get("status"))
    print("Extracted Invoice:", final_state.get("invoice_data"))
    print("Verification Result:", final_state.get("verification_data", {}).get("verification_status"))
    print("Summary:", final_state.get("final_summary"))
    assert final_state.get("status") == "COMPLETED"
    print("[PASS] SCENARIO 1 PASSED!")

async def run_scenario_2():
    print("\n=======================================================")
    print("RUNNING SCENARIO 2: Failure Detection & Autonomous Recovery")
    print("=======================================================")
    init_db()

    initial_state: AgentState = {
        "task_id": "test-task-sc2",
        "original_goal": "Process the latest invoice from Acme Corp with recovery demo.",
        "target_company": None,
        "interpreted_objective": None,
        "status": "PENDING",
        "plan": [],
        "current_step_index": 0,
        "step_count": 0,
        "max_steps": 15,
        "discovered_files": [],
        "selected_invoice_file": None,
        "invoice_data": None,
        "finance_record": None,
        "verification_data": None,
        "evidence_bundle": {},
        "current_tool": None,
        "current_tool_args": None,
        "last_tool_result": None,
        "execution_history": [],
        "error_message": None,
        "is_recoverable": True,
        "retry_count": 0,
        "max_retries": 3,
        "simulate_failure": True,  # Triggers 1st-attempt validation error!
        "recovery_strategy": None,
        "approval_required": False,
        "approval_status": "NONE",
        "approval_details": None,
        "final_summary": None
    }

    final_state = await agent_app.ainvoke(initial_state)
    print("\nFinal Agent Status:", final_state.get("status"))
    print("Retries performed:", final_state.get("retry_count"))
    print("Recovery strategy:", final_state.get("recovery_strategy"))
    print("Verification Status:", (final_state.get("verification_data") or {}).get("verification_status"))
    assert final_state.get("retry_count") >= 1
    assert final_state.get("status") == "COMPLETED"
    print("[PASS] SCENARIO 2 (RECOVERY) PASSED!")

async def run_scenario_3():
    print("\n=======================================================")
    print("RUNNING SCENARIO 3: Human-in-the-Loop Approval Threshold")
    print("=======================================================")
    init_db()

    initial_state: AgentState = {
        "task_id": "test-task-sc3",
        "original_goal": "Process the invoice from Enterprise Corp.",
        "target_company": None,
        "interpreted_objective": None,
        "status": "PENDING",
        "plan": [],
        "current_step_index": 0,
        "step_count": 0,
        "max_steps": 15,
        "discovered_files": [],
        "selected_invoice_file": None,
        "invoice_data": None,
        "finance_record": None,
        "verification_data": None,
        "evidence_bundle": {},
        "current_tool": None,
        "current_tool_args": None,
        "last_tool_result": None,
        "execution_history": [],
        "error_message": None,
        "is_recoverable": True,
        "retry_count": 0,
        "max_retries": 3,
        "simulate_failure": False,
        "recovery_strategy": None,
        "approval_required": False,
        "approval_status": "NONE",
        "approval_details": None,
        "final_summary": None
    }

    final_state = await agent_app.ainvoke(initial_state)
    print("\nFinal Agent Status:", final_state.get("status"))
    print("Approval Required:", final_state.get("approval_required"))
    print("Approval Details:", final_state.get("approval_details"))
    assert final_state.get("status") == "WAITING_FOR_APPROVAL"
    assert final_state.get("approval_required") is True
    print("[PASS] SCENARIO 3 (HUMAN APPROVAL PAUSE) PASSED!")

async def main():
    await run_scenario_1()
    await run_scenario_2()
    await run_scenario_3()

if __name__ == "__main__":
    asyncio.run(main())
