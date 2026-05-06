from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskIntent(str, Enum):
    ANSWER = "answer"
    SEARCH = "search"
    READ_LINK = "read_link"
    BROWSER = "browser"
    CODE = "code"
    EMAIL = "email"
    FILE = "file"
    DEPLOY = "deploy"
    DESKTOP_CONNECTOR = "desktop_connector"


class PlanAction(BaseModel):
    type: str
    label: str
    target: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentPlan(BaseModel):
    id: str = Field(default_factory=lambda: new_id("plan"))
    intent: TaskIntent
    summary: str
    risk: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    steps: list[str] = Field(default_factory=list)
    actions: list[PlanAction] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class AgentResult(BaseModel):
    answer: str
    status: str = "completed"
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, str]] = Field(default_factory=list)
    technical_details: dict[str, Any] = Field(default_factory=dict)
