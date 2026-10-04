from typing import Dict, Any
from .state import AgentState
from ..database.db import log_task_event
from ..tools.browser import FinanceBrowserAutomation
from ..tools.finance_tools import verify_invoice_direct

async def verify_result(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Performs strict, independent verification of the recorded invoice.
    Queries the finance system, compares expected vs actual fields, and ensures data integrity.
    """
    task_id = state["task_id"]
    invoice_data = state.get("invoice_data") or {}
    invoice_number = invoice_data.get("invoice_number", "")

    log_task_event(
        task_id=task_id,
        state="VERIFY",
        action="verify_result",
        tool="verify_invoice",
        status="info",
        message=f"Verification started for invoice {invoice_number}",
        details={"expected": invoice_data}
    )

    # First attempt verification through Playwright browser interaction
    browser = FinanceBrowserAutomation()
    verify_res = await browser.verify_invoice_in_system(invoice_number, invoice_data)

    # Fallback to direct DB check if browser had environmental issues
    if not verify_res["success"] and verify_res.get("status") != "MISMATCH":
        verify_res = verify_invoice_direct(invoice_number, invoice_data)

    evidence = state.get("evidence_bundle", {})
    if verify_res.get("evidence"):
        evidence["verification_screenshot"] = verify_res["evidence"]

    if verify_res.get("status") == "VERIFIED" or verify_res.get("success"):
        comparisons = verify_res.get("data", {}).get("comparisons", {})
        log_task_event(
            task_id=task_id,
            state="VERIFY",
            action="verify_result",
            tool="verify_invoice",
            status="success",
            message=f"[VERIFIED] Invoice verified: {invoice_number} ({invoice_data.get('company')}) recorded with 100% field parity",
            details={
                "status": "VERIFIED",
                "comparisons": comparisons,
                "finance_record": verify_res.get("data", {}).get("finance_record")
            }
        )

        return {
            "verification_data": verify_res.get("data"),
            "finance_record": verify_res.get("data", {}).get("finance_record"),
            "evidence_bundle": evidence,
            "status": "COMPLETED"
        }
    else:
        err_msg = verify_res.get("error") or "Field mismatch during finance ledger audit"
        log_task_event(
            task_id=task_id,
            state="VERIFY",
            action="verify_result",
            tool="verify_invoice",
            status="error",
            message=f"Verification failed: {err_msg}",
            details={"verification_details": verify_res}
        )

        return {
            "verification_data": verify_res,
            "error_message": err_msg,
            "evidence_bundle": evidence,
            "status": "FAILED"
        }
