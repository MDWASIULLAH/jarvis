from __future__ import annotations

from functools import lru_cache
from typing import Any

from backend.app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Any | None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    try:
        from supabase import create_client

        return create_client(settings.supabase_url, settings.supabase_service_role_key)
    except Exception:
        return None


async def persist_task_snapshot(table: str, payload: dict[str, Any]) -> None:
    client = get_supabase_client()
    if not client:
        return
    try:
        client.table(table).upsert(payload).execute()
    except Exception:
        return
