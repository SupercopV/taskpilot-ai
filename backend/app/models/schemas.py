from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TaskCreateRequest(BaseModel):
    goal: str = Field(..., description="Natural language enterprise goal for the autonomous agent")
    simulate_failure: bool = Field(False, description="Simulate temporary validation failure on 1st submission to demonstrate recovery")

class TaskApprovalRequest(BaseModel):
    feedback: Optional[str] = Field(None, description="Optional user note or feedback for approval")

class TaskRejectRequest(BaseModel):
    reason: Optional[str] = Field("Rejected by user during human-in-the-loop review", description="Reason for rejection")

class TaskEventResponse(BaseModel):
    id: int
    task_id: str
    timestamp: str
    state: str
    action: str
    tool: Optional[str] = None
    status: str
    message: str
    details: Dict[str, Any] = {}

class PlanStep(BaseModel):
    step_id: int
    title: str
    description: str
    tool: str
    status: str = "pending"  # pending, executing, completed, failed, skipped

class TaskStatusResponse(BaseModel):
    task_id: str
    goal: str
    status: str  # PENDING, PLANNING, EXECUTING, WAITING_FOR_APPROVAL, RECOVERING, VERIFYING, COMPLETED, FAILED, REJECTED
    company: Optional[str] = None
    plan: List[PlanStep] = []
    current_step_index: int = 0
    approval_status: str = "NONE"  # NONE, REQUESTED, APPROVED, REJECTED
    approval_request: Optional[Dict[str, Any]] = None
    extracted_invoice: Optional[Dict[str, Any]] = None
    finance_record: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    created_at: str
    updated_at: str

class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    goal: str
    company: Optional[str] = None
    invoice: Optional[Dict[str, Any]] = None
    finance_record: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    evidence: Dict[str, Any] = {}
    summary: str
    timeline: List[TaskEventResponse] = []

class FinanceInvoiceCreate(BaseModel):
    company: str
    invoice_number: str
    amount: float
    currency: str = "INR"
    due_date: str
    notes: Optional[str] = None
    simulate_failure: bool = False

class FinanceInvoiceResponse(BaseModel):
    record_id: str
    company: str
    invoice_number: str
    amount: float
    currency: str
    due_date: str
    status: str
    notes: Optional[str] = None
    created_at: str
