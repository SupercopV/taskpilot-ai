import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pathlib import Path

from ..config import settings
from ..models.schemas import (
    TaskCreateRequest, TaskStatusResponse, TaskResultResponse,
    TaskApprovalRequest, TaskRejectRequest, TaskEventResponse,
    FinanceInvoiceCreate, FinanceInvoiceResponse
)
from ..database.db import get_db_connection, log_task_event, get_task_events
from ..agent.graph import agent_app
from ..agent.state import AgentState
from ..tools.finance_tools import record_invoice_direct, get_finance_invoice_by_number
from .websocket import ws_manager

router = APIRouter()

# In-memory dictionary of running agent tasks and their states
# task_id -> current AgentState
ACTIVE_AGENT_STATES: Dict[str, AgentState] = {}
ACTIVE_ASYNC_TASKS: Dict[str, asyncio.Task] = {}

async def run_agent_workflow(task_id: str, state: AgentState):
    """
    Background worker that runs the LangGraph agent and broadcasts live events.
    """
    current_state = dict(state)
    ACTIVE_AGENT_STATES[task_id] = current_state
    try:
        # Stream each node execution in real-time
        async for chunk in agent_app.astream(state):
            for node_name, node_output in chunk.items():
                if isinstance(node_output, dict):
                    current_state.update(node_output)

            ACTIVE_AGENT_STATES[task_id] = current_state
            status = current_state.get("status", "EXECUTING")

            # Persist intermediate state to DB
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat() + "Z"
                cursor.execute("""
                UPDATE tasks 
                SET status = ?, company = ?, plan_json = ?, current_step_index = ?, 
                    state_json = ?, approval_status = ?, updated_at = ?
                WHERE task_id = ?;
                """, (
                    status,
                    current_state.get("target_company"),
                    json.dumps(current_state.get("plan", [])),
                    current_state.get("current_step_index", 0),
                    json.dumps(current_state, default=str),
                    current_state.get("approval_status", "NONE"),
                    now,
                    task_id
                ))
                conn.commit()
                conn.close()
            except Exception:
                pass

            # Broadcast step update to frontend in real time
            await ws_manager.broadcast_event(task_id, {
                "type": "STATUS_UPDATE",
                "task_id": task_id,
                "status": status,
                "current_step_index": current_state.get("current_step_index", 0),
                "approval_status": current_state.get("approval_status", "NONE"),
                "approval_details": current_state.get("approval_details"),
                "invoice_data": current_state.get("invoice_data"),
                "verification": current_state.get("verification_data"),
                "summary": current_state.get("final_summary")
            })

    except Exception as e:
        error_msg = f"Task execution encountered unhandled error: {str(e)}"
        print(f"Error in task {task_id}: {error_msg}")
        log_task_event(
            task_id=task_id,
            state="ERROR",
            action="run_agent_workflow",
            status="error",
            message=error_msg
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat() + "Z"
        cursor.execute("UPDATE tasks SET status = 'FAILED', updated_at = ? WHERE task_id = ?;", (now, task_id))
        conn.commit()
        conn.close()

        await ws_manager.broadcast_event(task_id, {
            "type": "STATUS_UPDATE",
            "task_id": task_id,
            "status": "FAILED",
            "error": error_msg
        })

# -------------------------------------------------------------
# CORE TASK API ENDPOINTS
# -------------------------------------------------------------

@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(req: TaskCreateRequest, background_tasks: BackgroundTasks):
    """
    Submits a natural-language goal and initiates an autonomous agent task.
    """
    task_id = f"task_{uuid.uuid4().hex[:10]}"
    now = datetime.utcnow().isoformat() + "Z"

    # Initial Agent State
    initial_state: AgentState = {
        "task_id": task_id,
        "original_goal": req.goal,
        "target_company": None,
        "interpreted_objective": None,
        "status": "PLANNING",
        "plan": [],
        "current_step_index": 0,
        "step_count": 0,
        "max_steps": settings.MAX_AGENT_STEPS,
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
        "max_retries": settings.MAX_RETRIES,
        "simulate_failure": req.simulate_failure,
        "recovery_strategy": None,
        "approval_required": False,
        "approval_status": "NONE",
        "approval_details": None,
        "final_summary": None
    }

    # Persist in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tasks (task_id, goal, status, state_json, created_at, updated_at)
    VALUES (?, ?, 'PLANNING', ?, ?, ?);
    """, (task_id, req.goal, json.dumps(initial_state, default=str), now, now))
    conn.commit()
    conn.close()

    # Log initial receipt event
    log_task_event(
        task_id=task_id,
        state="RECEIVE_GOAL",
        action="create_task",
        status="info",
        message=f"Autonomous agent received goal: '{req.goal}'",
        details={"goal": req.goal, "simulate_failure": req.simulate_failure}
    )

    # Launch background agent execution
    task_runner = asyncio.create_task(run_agent_workflow(task_id, initial_state))
    ACTIVE_ASYNC_TASKS[task_id] = task_runner

    return {
        "task_id": task_id,
        "status": "PLANNING",
        "goal": req.goal,
        "simulate_failure": req.simulate_failure,
        "created_at": now
    }

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Returns current status, active plan, current step, and extracted metadata for a task.
    """
    # Check in-memory state first for lowest latency
    state = ACTIVE_AGENT_STATES.get(task_id)
    if state:
        return TaskStatusResponse(
            task_id=task_id,
            goal=state["original_goal"],
            status=state["status"],
            company=state.get("target_company"),
            plan=state.get("plan", []),
            current_step_index=state.get("current_step_index", 0),
            approval_status=state.get("approval_status", "NONE"),
            approval_request=state.get("approval_details"),
            extracted_invoice=state.get("invoice_data"),
            finance_record=state.get("finance_record"),
            verification=state.get("verification_data"),
            summary=state.get("final_summary"),
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z"
        )

    # Query database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?;", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    state_data = json.loads(row["state_json"]) if row["state_json"] else {}
    plan_data = json.loads(row["plan_json"]) if row["plan_json"] else []

    return TaskStatusResponse(
        task_id=row["task_id"],
        goal=row["goal"],
        status=row["status"],
        company=row["company"],
        plan=plan_data,
        current_step_index=row["current_step_index"] or 0,
        approval_status=row["approval_status"] or "NONE",
        approval_request=state_data.get("approval_details"),
        extracted_invoice=state_data.get("invoice_data"),
        finance_record=state_data.get("finance_record"),
        verification=state_data.get("verification_data"),
        summary=state_data.get("final_summary"),
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

@router.get("/tasks/{task_id}/events", response_model=List[TaskEventResponse])
async def get_task_events_api(task_id: str):
    """
    Returns full chronological execution event timeline for observability.
    """
    events = get_task_events(task_id)
    return events

@router.post("/tasks/{task_id}/approve", response_model=Dict[str, Any])
async def approve_task_action(task_id: str, req: Optional[TaskApprovalRequest] = None):
    """
    Human-in-the-Loop: Approves a paused high-value invoice action and resumes execution.
    """
    state = ACTIVE_AGENT_STATES.get(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Active task state not found or already completed")

    if state.get("status") != "WAITING_FOR_APPROVAL":
        raise HTTPException(status_code=400, detail=f"Task is in status {state.get('status')}, not WAITING_FOR_APPROVAL")

    state["approval_status"] = "APPROVED"
    state["approval_required"] = False
    state["status"] = "EXECUTING"

    log_task_event(
        task_id=task_id,
        state="APPROVAL",
        action="approve_task_action",
        status="success",
        message="User confirmed human approval. Resuming autonomous workflow.",
        details={"feedback": req.feedback if req else None}
    )

    # Resume agent
    task_runner = asyncio.create_task(run_agent_workflow(task_id, state))
    ACTIVE_ASYNC_TASKS[task_id] = task_runner

    return {
        "task_id": task_id,
        "status": "EXECUTING",
        "approval_status": "APPROVED",
        "message": "Approval received. Agent resuming execution."
    }

@router.post("/tasks/{task_id}/reject", response_model=Dict[str, Any])
async def reject_task_action(task_id: str, req: Optional[TaskRejectRequest] = None):
    """
    Human-in-the-Loop: Rejects a sensitive invoice action and halts agent execution safely.
    """
    state = ACTIVE_AGENT_STATES.get(task_id)
    reason = req.reason if req and req.reason else "Rejected by user during human-in-the-loop governance"

    log_task_event(
        task_id=task_id,
        state="APPROVAL",
        action="reject_task_action",
        status="error",
        message=f"Task action rejected by user: {reason}. Autonomous execution halted.",
        details={"reason": reason}
    )

    if state:
        state["approval_status"] = "REJECTED"
        state["status"] = "REJECTED"
        state["error_message"] = reason

    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    cursor.execute("""
    UPDATE tasks 
    SET status = 'REJECTED', approval_status = 'REJECTED', updated_at = ?
    WHERE task_id = ?;
    """, (now, task_id))
    conn.commit()
    conn.close()

    await ws_manager.broadcast_event(task_id, {
        "type": "STATUS_UPDATE",
        "task_id": task_id,
        "status": "REJECTED",
        "reason": reason
    })

    return {
        "task_id": task_id,
        "status": "REJECTED",
        "approval_status": "REJECTED",
        "message": "Task rejected and terminated safely."
    }

@router.get("/tasks/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(task_id: str):
    """
    Returns final completion evidence, verification comparison, and natural language summary.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?;", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    state = ACTIVE_AGENT_STATES.get(task_id)
    state_data = state or (json.loads(row["state_json"]) if row["state_json"] else {})
    events = get_task_events(task_id)

    return TaskResultResponse(
        task_id=task_id,
        status=row["status"],
        goal=row["goal"],
        company=row["company"] or state_data.get("target_company"),
        invoice=state_data.get("invoice_data"),
        finance_record=state_data.get("finance_record"),
        verification=state_data.get("verification_data"),
        evidence=state_data.get("evidence_bundle", {}),
        summary=state_data.get("final_summary") or "Task processing in progress",
        timeline=events
    )

# -------------------------------------------------------------
# SYSTEM HEALTH & FILE ACCESS
# -------------------------------------------------------------

@router.get("/health")
async def health_check():
    """
    Health check endpoint reporting API status, LLM configuration, and environment.
    """
    from ..agent.llm import llm_service
    return {
        "status": "ok",
        "service": "TaskPilot AI Autonomous Engine",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_configured": llm_service.is_configured(),
        "playwright_headless": settings.PLAYWRIGHT_HEADLESS,
        "version": "1.0.0"
    }

@router.get("/invoices/{filename}")
async def get_invoice_file(filename: str):
    """
    Serves generated simulated invoice PDF files for evidence preview.
    """
    filepath = Path(settings.INVOICES_DIR) / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Invoice PDF not found")
    return FileResponse(filepath, media_type="application/pdf", filename=filename)

@router.get("/screenshots/{filename}")
async def get_screenshot_file(filename: str):
    """
    Serves Playwright browser automation screenshots for evidence preview.
    """
    filepath = Path(settings.SCREENSHOTS_DIR) / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(filepath, media_type="image/png")

# -------------------------------------------------------------
# MOCK FINANCE ERP REST ENDPOINTS
# -------------------------------------------------------------

@router.get("/finance/api/invoices")
async def get_all_finance_invoices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT record_id, company, invoice_number, amount, currency, due_date, status, notes, created_at
    FROM finance_invoices
    ORDER BY id DESC;
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/finance/api/invoices")
async def submit_finance_invoice_api(payload: FinanceInvoiceCreate):
    # Failure Simulation for Recovery Demo
    if payload.simulate_failure:
        raise HTTPException(
            status_code=422,
            detail="Temporary validation error. Please retry."
        )

    res = record_invoice_direct(
        company=payload.company,
        invoice_number=payload.invoice_number,
        amount=payload.amount,
        currency=payload.currency,
        due_date=payload.due_date,
        notes=payload.notes
    )
    return res["data"]

@router.get("/finance/api/invoices/{invoice_number}")
async def get_finance_invoice_by_num(invoice_number: str):
    rec = get_finance_invoice_by_number(invoice_number)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found in finance ledger")
    return rec
