from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.app.core import paths as _paths  # noqa: F401
from backend.app.models.task import ApprovalRequest, CreateTaskRequest, TaskRecord, TaskStatus
from backend.app.services.auth import CurrentUser, get_current_user
from backend.app.services.task_runner import run_task
from backend.app.services.task_store import task_store

from jarvis_agent.planner import JarvisPlanner

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskRecord)
async def create_task(
    payload: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskRecord:
    planner = JarvisPlanner()
    plan = planner.plan(payload.prompt)
    status = TaskStatus.WAITING_APPROVAL if plan.requires_approval else TaskStatus.QUEUED
    record = TaskRecord(
        user_id=current_user.user_id or payload.user_id,
        session_id=payload.session_id,
        prompt=payload.prompt,
        status=status,
        plan=plan.model_dump(mode="json"),
    )
    await task_store.create(record)
    await task_store.emit(record.id, "planned", plan.summary, {"plan": record.plan})
    if status == TaskStatus.QUEUED:
        background_tasks.add_task(run_task, record.id, task_store)
    return record


@router.get("/{task_id}", response_model=TaskRecord)
async def get_task(task_id: str) -> TaskRecord:
    record = await task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return record


@router.post("/{task_id}/approve", response_model=TaskRecord)
async def approve_task(task_id: str, payload: ApprovalRequest, background_tasks: BackgroundTasks) -> TaskRecord:
    record = await task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    if not payload.approved:
        cancelled = await task_store.update_status(task_id, TaskStatus.CANCELLED, "User cancelled the task.")
        return cancelled or record
    queued = await task_store.update_status(task_id, TaskStatus.QUEUED, "User approved the task.")
    background_tasks.add_task(run_task, task_id, task_store)
    return queued or record


@router.post("/{task_id}/cancel", response_model=TaskRecord)
async def cancel_task(task_id: str) -> TaskRecord:
    record = await task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    cancelled = await task_store.update_status(task_id, TaskStatus.CANCELLED, "Task cancelled.")
    return cancelled or record
