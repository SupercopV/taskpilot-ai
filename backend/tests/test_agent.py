import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.db import init_db
from app.agent.graph import agent_app
from app.agent.state import AgentState

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

@pytest.mark.asyncio
async def test_agent_standard_workflow():
    state: AgentState = {
        "task_id": "test_agent_std",
        "original_goal": "Find latest invoice from Acme Corp, extract amount and due date, enter into finance system, and verify.",
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

    result = await agent_app.ainvoke(state)
    assert result["status"] == "COMPLETED"
    assert result["invoice_data"]["invoice_number"] == "ACME-1024"
    assert result["invoice_data"]["amount"] == 48500.0
    assert result["verification_data"]["verification_status"] == "VERIFIED"

@pytest.mark.asyncio
async def test_agent_failure_and_recovery():
    state: AgentState = {
        "task_id": "test_agent_recovery",
        "original_goal": "Process latest invoice from Acme Corp.",
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
        "simulate_failure": True,  # Triggers 1st-attempt validation error
        "recovery_strategy": None,
        "approval_required": False,
        "approval_status": "NONE",
        "approval_details": None,
        "final_summary": None
    }

    result = await agent_app.ainvoke(state)
    assert result["status"] == "COMPLETED"
    assert result["retry_count"] >= 1
    assert result["recovery_strategy"] is not None
    assert result["verification_data"]["verification_status"] == "VERIFIED"

@pytest.mark.asyncio
async def test_agent_human_approval_pause():
    state: AgentState = {
        "task_id": "test_agent_approval",
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

    result = await agent_app.ainvoke(state)
    # Amount is INR 125,000 > 100,000 threshold
    assert result["status"] == "WAITING_FOR_APPROVAL"
    assert result["approval_required"] is True
    assert result["approval_details"]["amount"] == 125000.0

    # Test resuming upon approval
    result["approval_status"] = "APPROVED"
    resumed = await agent_app.ainvoke(result)
    assert resumed["status"] == "COMPLETED"
    assert resumed["verification_data"]["verification_status"] == "VERIFIED"
