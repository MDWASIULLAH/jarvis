from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.task_store import task_store

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/tasks/{task_id}")
async def task_events(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    record = await task_store.get(task_id)
    if record:
        await websocket.send_json({"type": "snapshot", "task": record.model_dump(mode="json")})
    try:
        async for event in task_store.subscribe(task_id):
            await websocket.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
