from __future__ import annotations

import asyncio
import json
import os
from typing import Any


class AsyncTaskQueue:
    """Redis-backed queue with in-memory fallback for local development."""

    def __init__(self, name: str = "jarvis:tasks") -> None:
        self.name = name
        self.redis_url = os.getenv("REDIS_URL")
        self._memory: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._redis = None

    async def connect(self) -> None:
        if not self.redis_url:
            return
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        except Exception:
            self._redis = None

    async def enqueue(self, payload: dict[str, Any]) -> None:
        if self._redis:
            await self._redis.lpush(self.name, json.dumps(payload))
            return
        await self._memory.put(payload)

    async def dequeue(self) -> dict[str, Any]:
        if self._redis:
            _, raw = await self._redis.brpop(self.name)
            return json.loads(raw)
        return await self._memory.get()
