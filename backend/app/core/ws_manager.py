import asyncio
import json
from typing import Any

from fastapi import WebSocket


class MonitorConnectionManager:
    """按试验任务 ID 管理 WebSocket 连接并广播监控帧。"""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, experiment_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(experiment_id, set()).add(websocket)

    async def disconnect(self, experiment_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(experiment_id)
            if conns and websocket in conns:
                conns.discard(websocket)
            if conns is not None and len(conns) == 0:
                self._connections.pop(experiment_id, None)

    def client_count(self, experiment_id: int) -> int:
        return len(self._connections.get(experiment_id, set()))

    async def broadcast(self, experiment_id: int, message: dict[str, Any]) -> None:
        async with self._lock:
            conns = list(self._connections.get(experiment_id, set()))
        await self._send_to_connections(experiment_id, conns, message)

    async def broadcast_all(self, message: dict[str, Any]) -> None:
        async with self._lock:
            pairs = [(eid, list(conns)) for eid, conns in self._connections.items()]
        for experiment_id, conns in pairs:
            await self._send_to_connections(experiment_id, conns, message)

    async def _send_to_connections(
        self,
        experiment_id: int,
        conns: list[WebSocket],
        message: dict[str, Any],
    ) -> None:
        if not conns:
            return
        text = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(experiment_id, ws)


ws_manager = MonitorConnectionManager()
