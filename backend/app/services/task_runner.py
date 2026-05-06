from __future__ import annotations

from backend.app.core import paths as _paths  # noqa: F401
from backend.app.models.task import TaskStatus
from backend.app.services.task_store import InMemoryTaskStore

from jarvis_agent.orchestrator import JarvisOrchestrator
from jarvis_agent.schemas import AgentPlan


async def run_task(task_id: str, store: InMemoryTaskStore) -> None:
    record = await store.get(task_id)
    if not record:
        return

    await store.update_status(task_id, TaskStatus.RUNNING, "Jarvis is executing the task.")
    try:
        orchestrator = JarvisOrchestrator()
        plan = AgentPlan.model_validate(record.plan)
        result = await orchestrator.run(record.prompt, plan)
        await store.set_result(task_id, result.model_dump(mode="json"))
    except Exception as exc:
        await store.set_error(task_id, f"Jarvis task failed: {exc}")
