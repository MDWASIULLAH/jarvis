from __future__ import annotations

import asyncio
import os

import httpx

from task_queue import AsyncTaskQueue


class BrowserWorker:
    def __init__(self) -> None:
        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")
        self.queue = AsyncTaskQueue()

    async def start(self) -> None:
        await self.queue.connect()
        while True:
            payload = await self.queue.dequeue()
            await self.handle(payload)

    async def handle(self, payload: dict) -> None:
        task_id = payload.get("task_id")
        if not task_id:
            return
        async with httpx.AsyncClient(timeout=60) as client:
            await client.post(f"{self.backend_url}/api/tasks/{task_id}/approve", json={"approved": True})


async def main() -> None:
    await BrowserWorker().start()


if __name__ == "__main__":
    asyncio.run(main())
