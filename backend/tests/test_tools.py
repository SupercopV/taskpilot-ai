import pytest
import os
import sys
from pathlib import Path

# Ensure backend directory is in python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.db import init_db
from app.tools.file_search import search_company_files
from app.tools.invoice_extractor import read_invoice_pdf, extract_invoice_fields, find_and_extract_latest_invoice
from app.tools.finance_tools import record_invoice_direct, verify_invoice_direct, get_finance_invoice_by_number

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_search_company_files():
    # Search for Acme Corp
    res = search_company_files("Acme Corp")
    assert res["success"] is True
    files = res["data"]["files"]
    assert len(files) >= 2
    assert "ACME_INV_1024.pdf" in files
    assert "ACME_INV_1023.pdf" in files

def test_extract_invoice_fields():
    res = extract_invoice_fields("ACME_INV_1024.pdf")
    assert res["success"] is True
    data = res["data"]
    assert "Acme" in data["company"]
    assert data["invoice_number"] == "ACME-1024"
    assert data["amount"] == 48500.0
    assert data["due_date"] == "2026-10-15"
    assert data["currency"] == "INR"

def test_find_and_extract_latest_invoice():
    candidates = ["ACME_INV_1023.pdf", "ACME_INV_1024.pdf"]
    res = find_and_extract_latest_invoice("Acme Corp", candidates)
    assert res["success"] is True
    latest = res["data"]
    # 1024 is dated 2026-10-01 vs 1023 dated 2026-08-10
    assert latest["invoice_number"] == "ACME-1024"
    assert latest["filename"] == "ACME_INV_1024.pdf"

def test_direct_finance_tools_record_and_verify():
    test_inv = {
        "company": "Test Vendor Corp",
        "invoice_number": "TEST-8899",
        "amount": 75000.0,
        "currency": "INR",
        "due_date": "2026-12-01",
        "notes": "Unit test direct record"
    }

    # Record
    rec_res = record_invoice_direct(**test_inv)
    assert rec_res["success"] is True
    assert "record_id" in rec_res["data"]

    # Verify matching
    ver_res = verify_invoice_direct("TEST-8899", test_inv)
    assert ver_res["success"] is True
    assert ver_res["status"] == "VERIFIED"
    assert ver_res["data"]["comparisons"]["amount"]["matched"] is True

    # Verify mismatch
    mismatch_expected = dict(test_inv)
    mismatch_expected["amount"] = 99999.0
    ver_fail = verify_invoice_direct("TEST-8899", mismatch_expected)
    assert ver_fail["success"] is False
    assert ver_fail["status"] == "MISMATCH"
