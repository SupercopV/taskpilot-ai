import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Finance Invoices Table (Mock Finance Portal System of Record)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS finance_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT UNIQUE NOT NULL,
        company TEXT NOT NULL,
        invoice_number TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'INR',
        due_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'RECORDED',
        notes TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Task Execution Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        goal TEXT NOT NULL,
        status TEXT NOT NULL,
        company TEXT,
        plan_json TEXT,
        current_step_index INTEGER DEFAULT 0,
        state_json TEXT,
        approval_status TEXT DEFAULT 'NONE',
        result_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Structured Execution Events Timeline Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        state TEXT NOT NULL,
        action TEXT NOT NULL,
        tool TEXT,
        status TEXT NOT NULL,
        message TEXT NOT NULL,
        details_json TEXT
    );
    """)

    # Seed initial existing invoices in finance portal if empty
    cursor.execute("SELECT COUNT(*) as count FROM finance_invoices;")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
        INSERT INTO finance_invoices (record_id, company, invoice_number, amount, currency, due_date, status, notes, created_at)
        VALUES 
        ('INV-1090', 'Acme Corp', 'ACME-1020', 25000.0, 'INR', '2026-05-15', 'PAID', 'Historical invoice Q1', '2026-05-01T10:00:00Z'),
        ('INV-1152', 'TechCorp Solutions', 'TC-650', 42000.0, 'INR', '2026-06-20', 'PAID', 'Historical invoice Q2', '2026-06-05T11:30:00Z');
        """)

    conn.commit()
    conn.close()

# Event logging helper
def log_task_event(
    task_id: str,
    state: str,
    action: str,
    message: str,
    status: str = "info",
    tool: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    timestamp = datetime.utcnow().isoformat() + "Z"
    details_json = json.dumps(details) if details else "{}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO task_events (task_id, timestamp, state, action, tool, status, message, details_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (task_id, timestamp, state, action, tool, status, message, details_json))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": event_id,
        "task_id": task_id,
        "timestamp": timestamp,
        "state": state,
        "action": action,
        "tool": tool,
        "status": status,
        "message": message,
        "details": details or {}
    }

def get_task_events(task_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, task_id, timestamp, state, action, tool, status, message, details_json
    FROM task_events
    WHERE task_id = ?
    ORDER BY id ASC
    """, (task_id,))
    rows = cursor.fetchall()
    conn.close()

    events = []
    for r in rows:
        events.append({
            "id": r["id"],
            "task_id": r["task_id"],
            "timestamp": r["timestamp"],
            "state": r["state"],
            "action": r["action"],
            "tool": r["tool"],
            "status": r["status"],
            "message": r["message"],
            "details": json.loads(r["details_json"]) if r["details_json"] else {}
        })
    return events
