from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Core Task & Intent
    task_id: str
    original_goal: str
    target_company: Optional[str]
    interpreted_objective: Optional[str]
    
    # State & Execution Plan
    status: str  # PENDING, PLANNING, EXECUTING, WAITING_FOR_APPROVAL, RECOVERING, VERIFYING, COMPLETED, FAILED, REJECTED
    plan: List[Dict[str, Any]]
    current_step_index: int
    step_count: int
    max_steps: int

    # Information & Evidence
    discovered_files: List[str]
    selected_invoice_file: Optional[str]
    invoice_data: Optional[Dict[str, Any]]
    finance_record: Optional[Dict[str, Any]]
    verification_data: Optional[Dict[str, Any]]
    evidence_bundle: Dict[str, Any]

    # Tool Execution State
    current_tool: Optional[str]
    current_tool_args: Optional[Dict[str, Any]]
    last_tool_result: Optional[Dict[str, Any]]
    execution_history: List[Dict[str, Any]]

    # Error, Failure Recovery & Retries
    error_message: Optional[str]
    is_recoverable: bool
    retry_count: int
    max_retries: int
    simulate_failure: bool
    recovery_strategy: Optional[str]

    # Human-in-the-Loop Governance
    approval_required: bool
    approval_status: str  # NONE, PENDING, APPROVED, REJECTED
    approval_details: Optional[Dict[str, Any]]

    # Completion
    final_summary: Optional[str]
