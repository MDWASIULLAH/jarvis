from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "ok": True,
        "name": settings.app_name,
        "environment": settings.environment,
        "supabase_configured": bool(settings.supabase_url),
        "llm_configured": bool(settings.openai_api_key),
    }
