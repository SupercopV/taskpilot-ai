import pytest
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
async def test_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "llm_provider" in data

@pytest.mark.asyncio
async def test_create_and_get_task():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_res = await client.post("/api/tasks", json={
            "goal": "Find latest invoice from Acme Corp and verify.",
            "simulate_failure": False
        })
        assert create_res.status_code == 200
        task_data = create_res.json()
        assert "task_id" in task_data
        task_id = task_data["task_id"]

        # Fetch status
        get_res = await client.get(f"/api/tasks/{task_id}")
        assert get_res.status_code == 200
        status_data = get_res.json()
        assert status_data["task_id"] == task_id
        assert status_data["goal"] == "Find latest invoice from Acme Corp and verify."

        # Fetch events
        events_res = await client.get(f"/api/tasks/{task_id}/events")
        assert events_res.status_code == 200
        assert isinstance(events_res.json(), list)

@pytest.mark.asyncio
async def test_finance_erp_api():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Submit invoice via REST
        inv_payload = {
            "company": "API Test Corp",
            "invoice_number": "APITEST-101",
            "amount": 54000.0,
            "currency": "INR",
            "due_date": "2026-11-20",
            "notes": "FastAPI test",
            "simulate_failure": False
        }
        post_res = await client.post("/api/finance/api/invoices", json=inv_payload)
        assert post_res.status_code == 200
        record = post_res.json()
        assert record["invoice_number"] == "APITEST-101"

        # List invoices
        list_res = await client.get("/api/finance/api/invoices")
        assert list_res.status_code == 200
        invoices = list_res.json()
        assert any(i["invoice_number"] == "APITEST-101" for i in invoices)

        # Test failure simulation flag
        fail_payload = dict(inv_payload)
        fail_payload["simulate_failure"] = True
        fail_res = await client.post("/api/finance/api/invoices", json=fail_payload)
        assert fail_res.status_code == 422
        assert "Temporary validation error" in fail_res.json()["detail"]
