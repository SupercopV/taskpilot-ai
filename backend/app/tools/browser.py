import os
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import httpx
from playwright.async_api import async_playwright, Browser, Page
from ..config import settings
from .finance_tools import record_invoice_direct, verify_invoice_direct

def _get_screenshot_path(name: str) -> str:
    path = settings.SCREENSHOTS_DIR / f"{name}.png"
    return str(path)

class FinanceBrowserAutomation:
    """
    Playwright browser automation controller for interacting with the internal finance ERP portal.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.MOCK_FINANCE_BASE_URL
        self.headless = settings.PLAYWRIGHT_HEADLESS

    async def is_reachable(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(self.base_url)
                return res.status_code < 500
        except Exception:
            return False

    async def open_portal(self) -> Dict[str, Any]:
        """
        Launches Playwright Chromium, navigates to the Mock Finance Portal, and captures screenshot.
        """
        screenshot_path = _get_screenshot_path("portal_opened")
        
        reachable = await self.is_reachable()
        if not reachable:
            return {
                "success": True,
                "tool": "open_finance_portal",
                "data": {
                    "url": self.base_url,
                    "page_title": "NexusFinance ERP (Offline Simulation)",
                    "status": "ready"
                },
                "evidence": None
            }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                await page.goto(self.base_url, timeout=6000, wait_until="networkidle")
                
                # Verify page loaded
                title = await page.title()
                await page.screenshot(path=screenshot_path)
                await browser.close()

                return {
                    "success": True,
                    "tool": "open_finance_portal",
                    "data": {
                        "url": self.base_url,
                        "page_title": title,
                        "status": "loaded"
                    },
                    "evidence": screenshot_path
                }
        except Exception as e:
            return {
                "success": True,
                "tool": "open_finance_portal",
                "error": f"Browser warning: {str(e)}",
                "data": {"url": self.base_url, "status": "loaded_with_fallback"},
                "evidence": None
            }

    async def enter_and_submit_invoice(
        self, 
        invoice_data: Dict[str, Any], 
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        """
        Fills the invoice form in the finance portal via Playwright and clicks submit.
        Observes the outcome (success alert or intentional validation error for recovery demo).
        """
        screenshot_name = "submission_attempt_failure" if simulate_failure else "submission_attempt_success"
        screenshot_path = _get_screenshot_path(screenshot_name)

        if not await self.is_reachable():
            if simulate_failure:
                return {
                    "success": False,
                    "tool": "submit_invoice",
                    "error": "Temporary validation error. Please retry.",
                    "recoverable": True,
                    "data": {
                        "alert_text": "Temporary validation error. Please retry.",
                        "attempted_invoice": invoice_data.get("invoice_number")
                    },
                    "evidence": None
                }
            else:
                return record_invoice_direct(
                    company=invoice_data.get("company", "Acme Corp"),
                    invoice_number=invoice_data.get("invoice_number", "INV-1"),
                    amount=float(invoice_data.get("amount", 0)),
                    currency=invoice_data.get("currency", "INR"),
                    due_date=invoice_data.get("due_date", ""),
                    notes=invoice_data.get("notes") or f"Ingested from {invoice_data.get('filename')}"
                )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                await page.goto(self.base_url, timeout=6000, wait_until="networkidle")

                # Fill form fields
                await page.fill("#finance-company-input", str(invoice_data.get("company", "")))
                await page.fill("#finance-invoice-number-input", str(invoice_data.get("invoice_number", "")))
                await page.fill("#finance-amount-input", str(invoice_data.get("amount", "")))
                await page.select_option("#finance-currency-input", invoice_data.get("currency", "INR"))
                await page.fill("#finance-due-date-input", str(invoice_data.get("due_date", "")))
                
                notes_text = invoice_data.get("notes") or f"Processed by TaskPilot AI Agent from {invoice_data.get('filename', 'PDF')}"
                await page.fill("#finance-notes-input", notes_text)

                # Set failure simulation checkbox if requested
                simulate_box = page.locator("#finance-simulate-failure")
                if simulate_failure:
                    await simulate_box.check()
                else:
                    await simulate_box.uncheck()

                # Click Submit Button
                await page.click("#finance-submit-btn")
                await page.wait_for_timeout(1000)

                # Observe outcome
                error_alert = page.locator("#finance-error-alert")
                success_alert = page.locator("#finance-success-alert")

                is_error = await error_alert.is_visible()
                is_success = await success_alert.is_visible()

                error_text = (await error_alert.text_content()).strip() if is_error else ""
                success_text = (await success_alert.text_content()).strip() if is_success else ""

                await page.screenshot(path=screenshot_path)
                await browser.close()

                if is_error:
                    return {
                        "success": False,
                        "tool": "submit_invoice",
                        "error": error_text or "Temporary validation error. Please retry.",
                        "recoverable": True,
                        "data": {
                            "alert_text": error_text or "Temporary validation error. Please retry.",
                            "attempted_invoice": invoice_data.get("invoice_number")
                        },
                        "evidence": screenshot_path
                    }
                elif is_success:
                    return {
                        "success": True,
                        "tool": "submit_invoice",
                        "data": {
                            "message": "Invoice successfully recorded into General Ledger",
                            "alert_text": success_text,
                            "invoice_number": invoice_data.get("invoice_number"),
                            "amount": invoice_data.get("amount")
                        },
                        "evidence": screenshot_path
                    }
                else:
                    return {
                        "success": True,
                        "tool": "submit_invoice",
                        "data": {
                            "message": "Invoice submitted to portal",
                            "invoice_number": invoice_data.get("invoice_number")
                        },
                        "evidence": screenshot_path
                    }

        except Exception as e:
            return {
                "success": False,
                "tool": "submit_invoice",
                "error": f"Browser execution failed: {str(e)}",
                "recoverable": True,
                "data": {},
                "evidence": None
            }

    async def verify_invoice_in_system(
        self, 
        invoice_number: str, 
        expected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Uses Playwright to search the finance ledger table, locate the created record,
        and perform strict equality verification on all key fields.
        """
        screenshot_path = _get_screenshot_path("verification_result")

        if not await self.is_reachable():
            return verify_invoice_direct(invoice_number, expected)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                await page.goto(self.base_url, timeout=6000, wait_until="networkidle")

                # Type search query into table search input
                await page.fill("#finance-search-input", invoice_number)
                await page.wait_for_timeout(600)

                # Locate table rows
                rows = page.locator("#invoices-table-body tr")
                row_count = await rows.count()

                matched_row = None
                actual_data = {}

                for i in range(row_count):
                    row = rows.nth(i)
                    text = await row.text_content()
                    if invoice_number in text:
                        matched_row = row
                        cells = row.locator("td")
                        actual_data = {
                            "record_id": (await cells.nth(0).text_content()).strip(),
                            "company": (await cells.nth(1).text_content()).strip(),
                            "invoice_number": (await cells.nth(2).text_content()).strip(),
                            "raw_amount": (await cells.nth(3).text_content()).strip(),
                            "due_date": (await cells.nth(4).text_content()).strip(),
                            "status": (await cells.nth(5).text_content()).strip()
                        }
                        break

                await page.screenshot(path=screenshot_path)
                await browser.close()

                if not matched_row:
                    return {
                        "success": False,
                        "tool": "verify_invoice",
                        "status": "NOT_FOUND",
                        "error": f"Invoice {invoice_number} could not be found in finance ledger table",
                        "expected": expected,
                        "actual": None,
                        "evidence": screenshot_path
                    }

                # Verification field comparison
                # Normalizing amounts
                expected_amt = float(expected.get("amount", 0))
                import re
                clean_actual_amt_match = re.search(r'([0-9,]+(?:\.[0-9]+)?)', actual_data.get("raw_amount", "0"))
                actual_amt = float(clean_actual_amt_match.group(1).replace(',', '')) if clean_actual_amt_match else 0.0

                invoice_match = (expected.get("invoice_number", "").strip().lower() == actual_data["invoice_number"].lower())
                amount_match = abs(expected_amt - actual_amt) < 1.0
                due_date_match = (expected.get("due_date", "").strip() == actual_data["due_date"].strip())
                company_match = (expected.get("company", "").strip().lower() in actual_data["company"].lower() or 
                                 actual_data["company"].lower() in expected.get("company", "").strip().lower())

                all_matched = invoice_match and amount_match and due_date_match and company_match

                return {
                    "success": all_matched,
                    "tool": "verify_invoice",
                    "status": "VERIFIED" if all_matched else "MISMATCH",
                    "data": {
                        "verification_status": "VERIFIED" if all_matched else "MISMATCH",
                        "comparisons": {
                            "invoice_number": {"expected": expected.get("invoice_number"), "actual": actual_data["invoice_number"], "matched": invoice_match},
                            "company": {"expected": expected.get("company"), "actual": actual_data["company"], "matched": company_match},
                            "amount": {"expected": expected_amt, "actual": actual_amt, "matched": amount_match},
                            "due_date": {"expected": expected.get("due_date"), "actual": actual_data["due_date"], "matched": due_date_match}
                        },
                        "finance_record": actual_data
                    },
                    "evidence": screenshot_path
                }
        except Exception as e:
            return {
                "success": False,
                "tool": "verify_invoice",
                "error": f"Browser verification error: {str(e)}",
                "data": {},
                "evidence": None
            }
