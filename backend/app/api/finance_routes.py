from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..database.db import get_db_connection
from ..models.schemas import FinanceInvoiceCreate, FinanceInvoiceResponse
from ..tools.finance_tools import record_invoice_direct, get_finance_invoice_by_number

finance_router = APIRouter()

@finance_router.get("/invoices")
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

@finance_router.post("/invoices")
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

@finance_router.get("/invoices/{invoice_number}")
async def get_finance_invoice_by_num(invoice_number: str):
    rec = get_finance_invoice_by_number(invoice_number)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found in finance ledger")
    return rec
