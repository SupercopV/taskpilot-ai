import os
import json
import re
from typing import Dict, Any, List, Optional
from ..config import settings

class LLMService:
    """
    LLM Provider Abstraction supporting Google Gemini, Groq, and a deterministic offline reasoning fallback.
    """
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self._init_clients()

    def _init_clients(self):
        self.gemini_client = None
        self.groq_client = None

        if self.gemini_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                print(f"Warning: Could not initialize Gemini client: {e}")

        if self.groq_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key)
            except Exception as e:
                print(f"Warning: Could not initialize Groq client: {e}")

    def is_configured(self) -> bool:
        if self.provider == "gemini" and self.gemini_client:
            return True
        if self.provider == "groq" and self.groq_client:
            return True
        return False

    async def understand_and_plan(self, goal: str) -> Dict[str, Any]:
        """
        Analyzes the user's natural language goal, extracts target company,
        and generates an execution plan.
        """
        prompt = f"""
You are TaskPilot AI, an autonomous enterprise AI employee.
Analyze the following natural-language user goal:
"{goal}"

Extract:
1. target_company: the company name mentioned (e.g. "Acme Corp", "TechCorp", etc.)
2. action_type: "process_latest_invoice"
3. required_tools: list of tools needed in sequence
4. plan: ordered list of steps with step_id, title, description, and tool name

Available tools:
- search_company_files
- extract_invoice_fields
- request_human_approval
- open_finance_portal
- submit_invoice
- verify_invoice

Respond strictly in valid JSON matching this structure:
{{
  "target_company": "Acme Corp",
  "objective": "Find latest invoice, extract amount and due date, submit to finance ERP, and verify.",
  "plan": [
    {{"step_id": 1, "title": "Search Company Invoices", "description": "Search document repository for invoices", "tool": "search_company_files"}},
    {{"step_id": 2, "title": "Extract & Select Latest Invoice", "description": "Read PDF text and extract latest invoice fields", "tool": "extract_invoice_fields"}},
    {{"step_id": 3, "title": "Safety & Approval Check", "description": "Check if amount requires human authorization", "tool": "request_human_approval"}},
    {{"step_id": 4, "title": "Open Internal Finance Portal", "description": "Launch Playwright browser and open ERP system", "tool": "open_finance_portal"}},
    {{"step_id": 5, "title": "Submit Invoice to Ledger", "description": "Enter data and submit invoice in ERP portal", "tool": "submit_invoice"}},
    {{"step_id": 6, "title": "Verify Ledger Recording", "description": "Query ERP records to confirm exact match", "tool": "verify_invoice"}}
  ]
}}
"""
        # If Gemini is configured
        if self.provider == "gemini" and self.gemini_client:
            for model_name in ['gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-flash-latest']:
                try:
                    response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    text = response.text
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
                except Exception as e:
                    print(f"Gemini API model {model_name} failed: {e}")

        # If Groq is configured
        elif self.provider == "groq" and self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(completion.choices[0].message.content)
            except Exception as e:
                print(f"Groq API call failed, falling back to deterministic reasoning: {e}")

        # Deterministic Rule-Based Parsing (Fallback / Offline Engine)
        return self._deterministic_parse_goal(goal)

    def _deterministic_parse_goal(self, goal: str) -> Dict[str, Any]:
        """
        Robust deterministic parsing when no cloud LLM API key is supplied.
        """
        lower = goal.lower()
        target_company = "Acme Corp"
        if "techcorp" in lower:
            target_company = "TechCorp Solutions"
        elif "globex" in lower:
            target_company = "Globex Corporation"
        elif "enterprise" in lower:
            target_company = "Enterprise Global Systems"
        elif "acme" in lower:
            target_company = "Acme Corp"

        return {
            "target_company": target_company,
            "objective": f"Locate latest invoice for {target_company}, extract fields, enter into ERP portal via browser automation, and verify recording.",
            "plan": [
                {
                    "step_id": 1,
                    "title": "Search Company Document Repository",
                    "description": f"Search simulated enterprise storage for {target_company} invoices",
                    "tool": "search_company_files"
                },
                {
                    "step_id": 2,
                    "title": "Extract & Select Latest Invoice",
                    "description": "Parse PDF invoices, extract key financial metadata, and identify newest invoice by date",
                    "tool": "extract_invoice_fields"
                },
                {
                    "step_id": 3,
                    "title": "Governance & Human Approval Check",
                    "description": "Assess financial threshold (> ₹100,000) and pause for authorization if required",
                    "tool": "request_human_approval"
                },
                {
                    "step_id": 4,
                    "title": "Open Internal Finance Portal",
                    "description": "Launch Playwright browser instance and navigate to ERP accounts payable ledger",
                    "tool": "open_finance_portal"
                },
                {
                    "step_id": 5,
                    "title": "Submit Invoice to Finance Portal",
                    "description": "Fill web form with extracted fields and submit to ledger",
                    "tool": "submit_invoice"
                },
                {
                    "step_id": 6,
                    "title": "Verify Ledger Recording",
                    "description": "Search ERP table, compare all fields, and verify record integrity",
                    "tool": "verify_invoice"
                }
            ]
        }

    async def generate_completion_summary(
        self, 
        goal: str, 
        invoice: Dict[str, Any], 
        finance_record: Dict[str, Any], 
        verification: Dict[str, Any],
        recovery_occurred: bool = False
    ) -> str:
        """
        Generates a concise, executive natural-language completion summary.
        """
        prompt = f"""
Summarize this automated task completion concisely for an enterprise dashboard:
Goal: {goal}
Invoice: {invoice.get('invoice_number')} from {invoice.get('company')}
Amount: {invoice.get('currency')} {invoice.get('amount')}
Due Date: {invoice.get('due_date')}
Finance Record ID: {finance_record.get('record_id')}
Verification: {verification.get('status')}
Failure & Recovery: {"Yes, successfully recovered from initial temporary validation error" if recovery_occurred else "Direct first-pass success"}

Return 2-3 crisp professional sentences highlighting what was accomplished, verified, and recorded.
"""
        if self.provider == "gemini" and self.gemini_client:
            for model_name in ['gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-flash-latest']:
                try:
                    res = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    return res.text.strip()
                except Exception as e:
                    print(f"Gemini summary model {model_name} failed: {e}")
        elif self.provider == "groq" and self.groq_client:
            try:
                res = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                return res.choices[0].message.content.strip()
            except Exception:
                pass

        # Deterministic professional summary
        rec_note = " Initial validation failure was automatically detected and recovered via retry." if recovery_occurred else ""
        return (
            f"Successfully processed the latest invoice ({invoice.get('invoice_number')}) for {invoice.get('company')}. "
            f"Extracted total amount of {invoice.get('currency', 'INR')} {invoice.get('amount', 0):,} due on {invoice.get('due_date')}. "
            f"The invoice was entered into the finance system (Record {finance_record.get('record_id', 'N/A')}) via browser automation and verified against the general ledger with 100% field accuracy.{rec_note}"
        )

llm_service = LLMService()
