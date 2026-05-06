from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    PLANNED = "planned"
    WAITING_APPROVAL = "waiting_approval"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskEvent(BaseModel):
    type: str
    message: str
    created_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class CreateTaskRequest(BaseModel):
    prompt: str
    user_id: str | None = None
    session_id: str | None = None


class ApprovalRequest(BaseModel):
    approved: bool = True
    edited_payload: dict[str, Any] | None = None


class TaskRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:16]}")
    user_id: str | None = None
    session_id: str | None = None
    prompt: str
    status: TaskStatus
    plan: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    events: list[TaskEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
