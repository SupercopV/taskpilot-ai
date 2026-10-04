import json
import asyncio
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    """
    Manages active WebSocket connections for live task timeline streaming.
    """
    def __init__(self):
        # task_id -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = []
            self.active_connections[task_id].append(websocket)

    async def disconnect(self, task_id: str, websocket: WebSocket):
        async with self._lock:
            if task_id in self.active_connections:
                if websocket in self.active_connections[task_id]:
                    self.active_connections[task_id].remove(websocket)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]

    async def broadcast_event(self, task_id: str, event_data: dict):
        async with self._lock:
            connections = list(self.active_connections.get(task_id, []))
        
        for conn in connections:
            try:
                await conn.send_text(json.dumps(event_data))
            except Exception:
                await self.disconnect(task_id, conn)

ws_manager = ConnectionManager()
