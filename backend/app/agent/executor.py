from typing import Dict, Any, List
from .state import AgentState
from ..config import settings
from ..database.db import log_task_event
from ..tools.file_search import search_company_files
from ..tools.invoice_extractor import find_and_extract_latest_invoice
from ..tools.browser import FinanceBrowserAutomation
from ..tools.finance_tools import record_invoice_direct

async def select_tool(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Evaluates the plan and current step index,
    selecting the appropriate tool and arguments based on the state.
    """
    plan = state.get("plan", [])
    step_idx = state.get("current_step_index", 0)

    if step_idx < len(plan):
        current_step = plan[step_idx]
        tool_name = current_step.get("tool", "search_company_files")
        tool_args = {}

        if tool_name == "search_company_files":
            tool_args = {"query": state.get("target_company", "Acme Corp")}
        elif tool_name == "extract_invoice_fields":
            tool_args = {
                "company": state.get("target_company", "Acme Corp"),
                "files": state.get("discovered_files", [])
            }
        elif tool_name == "request_human_approval":
            tool_args = {"invoice_data": state.get("invoice_data", {})}
        elif tool_name == "submit_invoice":
            # Pass simulate_failure flag if this is the first attempt (retry_count == 0)
            is_failure_demo = state.get("simulate_failure", False) and (state.get("retry_count", 0) == 0)
            tool_args = {
                "invoice_data": state.get("invoice_data", {}),
                "simulate_failure": is_failure_demo
            }

        return {
            "current_tool": tool_name,
            "current_tool_args": tool_args,
            "status": "EXECUTING"
        }

    return {"status": "COMPLETED"}

async def execute_action(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Executes the selected tool, records structured evidence,
    and returns observations to the agent state.
    """
    task_id = state["task_id"]
    tool_name = state.get("current_tool")
    tool_args = state.get("current_tool_args") or {}
    evidence = state.get("evidence_bundle") or {}
    history = list(state.get("execution_history") or [])
    step_idx = state.get("current_step_index", 0)

    # 1. SEARCH COMPANY FILES
    if tool_name == "search_company_files":
        company = tool_args.get("query", state.get("target_company", "Acme Corp"))
        log_task_event(
            task_id=task_id,
            state="EXECUTING",
            action="execute_action",
            tool=tool_name,
            status="info",
            message=f"Searching company document repository for '{company}' invoices",
            details={"company": company}
        )
        res = search_company_files(company)
        files = res.get("data", {}).get("files", [])
        
        log_task_event(
            task_id=task_id,
            state="OBSERVE",
            action="observe_result",
            tool=tool_name,
            status="success" if res["success"] else "error",
            message=f"Found {len(files)} invoice document(s): {', '.join(files)}",
            details=res
        )

        history.append({"tool": tool_name, "result": res})
        evidence["discovered_files"] = files

        return {
            "discovered_files": files,
            "last_tool_result": res,
            "evidence_bundle": evidence,
            "execution_history": history,
            "current_step_index": step_idx + 1
        }

    # 2. EXTRACT INVOICE FIELDS
    elif tool_name == "extract_invoice_fields":
        files = state.get("discovered_files", [])
        company = state.get("target_company", "Acme Corp")
        log_task_event(
            task_id=task_id,
            state="EXECUTING",
            action="execute_action",
            tool=tool_name,
            status="info",
            message=f"Extracting and selecting newest invoice from {len(files)} candidate document(s)",
            details={"candidates": files}
        )
        res = find_and_extract_latest_invoice(company, files)
        inv_data = res.get("data", {})

        log_task_event(
            task_id=task_id,
            state="OBSERVE",
            action="observe_result",
            tool=tool_name,
            status="success" if res["success"] else "error",
            message=f"Invoice found and extracted: {inv_data.get('invoice_number')} | Amount: {inv_data.get('currency', 'INR')} {inv_data.get('amount', 0):,} | Due: {inv_data.get('due_date')}",
            details=res
        )

        history.append({"tool": tool_name, "result": res})
        evidence["invoice_data"] = inv_data
        evidence["source_pdf"] = inv_data.get("filename")

        return {
            "invoice_data": inv_data,
            "selected_invoice_file": inv_data.get("filename"),
            "last_tool_result": res,
            "evidence_bundle": evidence,
            "execution_history": history,
            "current_step_index": step_idx + 1
        }

    # 3. REQUEST HUMAN APPROVAL (GOVERNANCE CHECK)
    elif tool_name == "request_human_approval":
        inv_data = state.get("invoice_data") or {}
        amount = float(inv_data.get("amount", 0))
        threshold = float(settings.APPROVAL_THRESHOLD_INR)
        approval_status = state.get("approval_status", "NONE")

        # If rejected, halt execution
        if approval_status == "REJECTED":
            log_task_event(
                task_id=task_id,
                state="APPROVAL",
                action="request_human_approval",
                tool=tool_name,
                status="error",
                message=f"Action rejected by user during human-in-the-loop review. Execution halted safely.",
                details={"invoice": inv_data}
            )
            return {
                "status": "REJECTED",
                "error_message": "User rejected the invoice submission during human-in-the-loop governance."
            }

        # If already approved by user
        if approval_status == "APPROVED":
            log_task_event(
                task_id=task_id,
                state="APPROVAL",
                action="request_human_approval",
                tool=tool_name,
                status="success",
                message=f"Human approval confirmed for invoice {inv_data.get('invoice_number')}. Proceeding with submission.",
                details={"invoice": inv_data}
            )
            return {
                "approval_required": False,
                "current_step_index": step_idx + 1,
                "status": "EXECUTING"
            }

        # If amount exceeds threshold, pause for human approval!
        if amount > threshold:
            approval_msg = f"Human approval required before submitting invoice of {inv_data.get('currency', 'INR')} {amount:,.2f} (Threshold: {threshold:,.0f})."
            log_task_event(
                task_id=task_id,
                state="WAITING_FOR_APPROVAL",
                action="request_human_approval",
                tool=tool_name,
                status="warning",
                message=approval_msg,
                details={
                    "amount": amount,
                    "threshold": threshold,
                    "invoice": inv_data
                }
            )
            return {
                "approval_required": True,
                "approval_status": "PENDING",
                "approval_details": {
                    "company": inv_data.get("company"),
                    "invoice_number": inv_data.get("invoice_number"),
                    "amount": amount,
                    "currency": inv_data.get("currency", "INR"),
                    "due_date": inv_data.get("due_date"),
                    "reason": f"Amount exceeds safety threshold of INR {threshold:,.0f}"
                },
                "status": "WAITING_FOR_APPROVAL"
            }
        else:
            # Below threshold, proceed automatically
            log_task_event(
                task_id=task_id,
                state="APPROVAL",
                action="request_human_approval",
                tool=tool_name,
                status="info",
                message=f"Amount ({inv_data.get('currency', 'INR')} {amount:,.2f}) is within autonomous execution policy (<= {threshold:,.0f}). Automatic processing permitted.",
                details={"amount": amount, "threshold": threshold}
            )
            return {
                "approval_required": False,
                "current_step_index": step_idx + 1,
                "status": "EXECUTING"
            }

    # 4. OPEN FINANCE PORTAL
    elif tool_name == "open_finance_portal":
        log_task_event(
            task_id=task_id,
            state="EXECUTING",
            action="execute_action",
            tool=tool_name,
            status="info",
            message="Opening internal finance ERP portal via Playwright browser automation",
            details={}
        )
        browser = FinanceBrowserAutomation()
        res = await browser.open_portal()

        log_task_event(
            task_id=task_id,
            state="OBSERVE",
            action="observe_result",
            tool=tool_name,
            status="success" if res["success"] else "warning",
            message=f"Finance portal loaded ({res.get('data', {}).get('page_title', 'ERP')})",
            details=res
        )

        history.append({"tool": tool_name, "result": res})
        if res.get("evidence"):
            evidence["portal_opened_screenshot"] = res["evidence"]

        return {
            "last_tool_result": res,
            "evidence_bundle": evidence,
            "execution_history": history,
            "current_step_index": step_idx + 1
        }

    # 5. SUBMIT INVOICE
    elif tool_name == "submit_invoice":
        inv_data = state.get("invoice_data") or {}
        # Only simulate failure on attempt 0
        simulate_fail = state.get("simulate_failure", False) and (state.get("retry_count", 0) == 0)

        log_task_event(
            task_id=task_id,
            state="EXECUTING",
            action="execute_action",
            tool=tool_name,
            status="info",
            message=f"Entering and submitting invoice {inv_data.get('invoice_number')} into finance ledger form",
            details={"invoice": inv_data, "simulate_failure": simulate_fail}
        )

        browser = FinanceBrowserAutomation()
        res = await browser.enter_and_submit_invoice(inv_data, simulate_failure=simulate_fail)

        # Fallback to direct recording if browser could not connect to local host
        if not res["success"] and not res.get("recoverable"):
            res = record_invoice_direct(
                company=inv_data.get("company", "Acme Corp"),
                invoice_number=inv_data.get("invoice_number", "INV-1"),
                amount=inv_data.get("amount", 0.0),
                currency=inv_data.get("currency", "INR"),
                due_date=inv_data.get("due_date", ""),
                notes=f"Processed by TaskPilot AI Agent from {inv_data.get('filename')}"
            )

        history.append({"tool": tool_name, "result": res})
        if res.get("evidence"):
            evidence["submission_screenshot"] = res["evidence"]

        # Check if submission failed (controlled failure recovery demo)
        if not res["success"]:
            return {
                "last_tool_result": res,
                "evidence_bundle": evidence,
                "execution_history": history,
                "status": "DETECT_FAILURE"
            }

        log_task_event(
            task_id=task_id,
            state="OBSERVE",
            action="observe_result",
            tool=tool_name,
            status="success",
            message=f"Submission successful: Invoice {inv_data.get('invoice_number')} submitted to ledger",
            details=res
        )

        return {
            "last_tool_result": res,
            "evidence_bundle": evidence,
            "execution_history": history,
            "current_step_index": step_idx + 1
        }

    # 6. VERIFY INVOICE
    elif tool_name == "verify_invoice":
        return {"status": "VERIFYING"}

    # Default fallback
    return {"current_step_index": step_idx + 1}
