from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.services.ws_manager import broadcaster

router = APIRouter()


@router.websocket("/kanban")
async def kanban_ws(ws: WebSocket, token: str | None = Query(default=None)) -> None:
    if not token or decode_access_token(token) is None:
        await ws.close(code=1008)
        return
    await broadcaster.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await broadcaster.disconnect(ws)
