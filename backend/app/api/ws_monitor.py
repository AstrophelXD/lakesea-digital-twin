from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.core.ws_manager import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/monitor/{experiment_id}")
async def monitor_websocket(
    websocket: WebSocket,
    experiment_id: int,
    token: str = Query(...),
):
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(experiment_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(experiment_id, websocket)
