from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import AsyncIterator

from backend.app.models.task import TaskEvent, TaskRecord, TaskStatus, utc_now


class InMemoryTaskStore:
    """Development task store.

    Supabase/Postgres should be used for production persistence. This store keeps
    the API runnable in local Docker and preview environments.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = asyncio.Lock()
        self._subscribers: dict[str, list[asyncio.Queue[TaskEvent]]] = defaultdict(list)

    async def create(self, task: TaskRecord) -> TaskRecord:
        async with self._lock:
            self._tasks[task.id] = task
        await self.emit(task.id, "created", "Task created.", {"status": task.status})
        return task

    async def get(self, task_id: str) -> TaskRecord | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def update_status(self, task_id: str, status: TaskStatus, message: str) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            task.status = status
            task.updated_at = utc_now()
        await self.emit(task_id, "status", message, {"status": status})
        return task

    async def set_result(self, task_id: str, result: dict) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.updated_at = utc_now()
        await self.emit(task_id, "completed", "Task completed.", {"result": result})
        return task

    async def set_error(self, task_id: str, error: str) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            task.error = error
            task.status = TaskStatus.FAILED
            task.updated_at = utc_now()
        await self.emit(task_id, "failed", error, {})
        return task

    async def emit(self, task_id: str, event_type: str, message: str, payload: dict | None = None) -> None:
        event = TaskEvent(type=event_type, message=message, payload=payload or {})
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.events.append(event)
            subscribers = list(self._subscribers.get(task_id, []))
        for queue in subscribers:
            await queue.put(event)

    async def subscribe(self, task_id: str) -> AsyncIterator[TaskEvent]:
        queue: asyncio.Queue[TaskEvent] = asyncio.Queue()
        self._subscribers[task_id].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers[task_id].remove(queue)


task_store = InMemoryTaskStore()
