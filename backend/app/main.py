import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .database.db import init_db
from .api.routes import router as api_router
from .api.websocket import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables on startup
    init_db()
    print("[OK] TaskPilot AI Database & Tables initialized successfully.")
    yield
    print("Shutting down TaskPilot AI Server...")

app = FastAPI(
    title="TaskPilot AI API",
    description="Autonomous AI Agent for Enterprise Task Automation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("RENDER") or not settings.FRONTEND_URL else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api.finance_routes import finance_router

# Direct Finance API endpoints (for web portal AJAX and Playwright)
app.include_router(finance_router, prefix="/finance/api")
app.include_router(finance_router, prefix="/api/finance/api")

# API Router Mount
app.include_router(api_router, prefix="/api")

# WebSocket Endpoint for Real-time Task Timeline Streaming
@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_endpoint(websocket: WebSocket, task_id: str):
    await ws_manager.connect(task_id, websocket)
    try:
        while True:
            # Keep connection open; client may send ping or feedback
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(task_id, websocket)
    except Exception:
        await ws_manager.disconnect(task_id, websocket)

# Mount Mock Finance ERP Portal at /finance
mock_finance_dir = Path(__file__).resolve().parent.parent.parent / "mock-finance-app"
if not mock_finance_dir.exists():
    mock_finance_dir = Path("/app/mock-finance-app")
if not mock_finance_dir.exists():
    mock_finance_dir = Path(__file__).resolve().parent.parent / "mock-finance-app"
if mock_finance_dir.exists():
    app.mount("/finance", StaticFiles(directory=str(mock_finance_dir), html=True), name="finance_portal")

# Root redirect or API info
@app.get("/")
async def root():
    return {
        "product": "TaskPilot AI",
        "description": "Autonomous AI Agent for Enterprise Task Automation",
        "endpoints": {
            "api_health": "/api/health",
            "tasks": "/api/tasks",
            "mock_finance_portal": "/finance",
            "docs": "/docs"
        }
    }
