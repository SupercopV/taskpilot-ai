import pytest
import asyncio
import sys
from pathlib import Path
import httpx

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.database.db import init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

@pytest.mark.asyncio
async def test_end_to_end_standard_workflow():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create task
        res = await client.post("/api/tasks", json={
            "goal": "Find latest invoice from Acme Corp, extract amount and due date, enter into finance system, and verify.",
            "simulate_failure": False
        })
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        # 2. Wait for completion (give Playwright browser automation up to 30s)
        completed = False
        for _ in range(60):
            await asyncio.sleep(0.5)
            status_res = await client.get(f"/api/tasks/{task_id}")
            if status_res.status_code == 200 and status_res.json()["status"] == "COMPLETED":
                completed = True
                break

        assert completed is True, f"Task did not complete within timeout. Status: {status_res.json().get('status')}"

        # 3. Verify Result and Evidence
        result_res = await client.get(f"/api/tasks/{task_id}/result")
        assert result_res.status_code == 200
        data = result_res.json()
        assert data["status"] == "COMPLETED"
        assert data["invoice"]["invoice_number"] == "ACME-1024"
        assert data["invoice"]["amount"] == 48500.0
        assert data["verification"]["verification_status"] == "VERIFIED"
        assert len(data["timeline"]) >= 5

@pytest.mark.asyncio
async def test_end_to_end_human_approval_and_rejection():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Create task for Enterprise Corp (amount ₹125,000 > ₹100,000)
        res = await client.post("/api/tasks", json={
            "goal": "Process the invoice from Enterprise Corp.",
            "simulate_failure": False
        })
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        # Wait until paused in WAITING_FOR_APPROVAL
        waiting = False
        for _ in range(25):
            await asyncio.sleep(0.3)
            status_res = await client.get(f"/api/tasks/{task_id}")
            if status_res.status_code == 200 and status_res.json()["status"] == "WAITING_FOR_APPROVAL":
                waiting = True
                break

        assert waiting is True, "Task should pause for human approval on > 100k amount"

        # Reject the task
        reject_res = await client.post(f"/api/tasks/{task_id}/reject", json={
            "reason": "Amount exceeds unbudgeted Q4 expenditure limit"
        })
        assert reject_res.status_code == 200
        assert reject_res.json()["status"] == "REJECTED"

        # Confirm task ended in REJECTED state
        status_after = await client.get(f"/api/tasks/{task_id}")
        assert status_after.json()["status"] == "REJECTED"
