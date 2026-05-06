from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header

from backend.app.services.supabase import get_supabase_client


@dataclass
class CurrentUser:
    user_id: str | None = None
    email: str | None = None
    access_token: str | None = None


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        return CurrentUser()

    token = authorization.split(" ", 1)[1].strip()
    client = get_supabase_client()
    if not client:
        return CurrentUser(access_token=token)

    try:
        response = client.auth.get_user(token)
        user = response.user
        return CurrentUser(user_id=user.id, email=user.email, access_token=token)
    except Exception:
        return CurrentUser(access_token=token)
