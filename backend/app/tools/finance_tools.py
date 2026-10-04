import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..database.db import get_db_connection

def record_invoice_direct(
    company: str,
    invoice_number: str,
    amount: float,
    currency: str = "INR",
    due_date: str = "",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Direct ledger recording into SQLite database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate record ID e.g. INV-2841
    cursor.execute("SELECT COUNT(*) as count FROM finance_invoices;")
    count = cursor.fetchone()["count"]
    record_id = f"INV-{2800 + count + 1}"
    created_at = datetime.utcnow().isoformat() + "Z"

    # Check if duplicate
    cursor.execute("SELECT record_id FROM finance_invoices WHERE invoice_number = ?;", (invoice_number,))
    existing = cursor.fetchone()
    if existing:
        record_id = existing["record_id"]
        cursor.execute("""
        UPDATE finance_invoices 
        SET company = ?, amount = ?, currency = ?, due_date = ?, notes = ?, created_at = ?
        WHERE invoice_number = ?;
        """, (company, amount, currency, due_date, notes or "", created_at, invoice_number))
    else:
        cursor.execute("""
        INSERT INTO finance_invoices (record_id, company, invoice_number, amount, currency, due_date, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'RECORDED', ?, ?);
        """, (record_id, company, invoice_number, amount, currency, due_date, notes or "", created_at))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "tool": "enter_invoice_direct",
        "data": {
            "record_id": record_id,
            "company": company,
            "invoice_number": invoice_number,
            "amount": amount,
            "currency": currency,
            "due_date": due_date,
            "status": "RECORDED",
            "created_at": created_at
        },
        "evidence": f"Ledger Record {record_id}"
    }

def get_finance_invoice_by_number(invoice_number: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT record_id, company, invoice_number, amount, currency, due_date, status, notes, created_at
    FROM finance_invoices
    WHERE LOWER(invoice_number) = LOWER(?);
    """, (invoice_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def verify_invoice_direct(invoice_number: str, expected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct verification against the finance database records.
    """
    actual = get_finance_invoice_by_number(invoice_number)
    if not actual:
        return {
            "success": False,
            "tool": "verify_invoice_direct",
            "status": "NOT_FOUND",
            "error": f"Invoice {invoice_number} not found in finance ledger",
            "expected": expected,
            "actual": None,
            "evidence": None
        }

    expected_amt = float(expected.get("amount", 0))
    actual_amt = float(actual.get("amount", 0))

    invoice_match = (expected.get("invoice_number", "").strip().lower() == actual["invoice_number"].lower())
    amount_match = abs(expected_amt - actual_amt) < 0.01
    due_date_match = (expected.get("due_date", "").strip() == actual["due_date"].strip())
    company_match = (expected.get("company", "").strip().lower() in actual["company"].lower() or 
                     actual["company"].lower() in expected.get("company", "").strip().lower())

    all_matched = invoice_match and amount_match and due_date_match and company_match

    return {
        "success": all_matched,
        "tool": "verify_invoice_direct",
        "status": "VERIFIED" if all_matched else "MISMATCH",
        "data": {
            "verification_status": "VERIFIED" if all_matched else "MISMATCH",
            "comparisons": {
                "invoice_number": {"expected": expected.get("invoice_number"), "actual": actual["invoice_number"], "matched": invoice_match},
                "company": {"expected": expected.get("company"), "actual": actual["company"], "matched": company_match},
                "amount": {"expected": expected_amt, "actual": actual_amt, "matched": amount_match},
                "due_date": {"expected": expected.get("due_date"), "actual": actual["due_date"], "matched": due_date_match}
            },
            "finance_record": actual
        },
        "evidence": f"Database Record {actual['record_id']}"
    }
