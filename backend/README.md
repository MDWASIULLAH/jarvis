# Jarvis Cloud Backend

FastAPI service for Jarvis cloud mode.

## Run

```bash
uvicorn backend.app.main:app --reload --port 8000
```

## Main APIs

- `GET /health`
- `POST /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/approve`
- `POST /api/tasks/{task_id}/cancel`
- `WS /ws/tasks/{task_id}`
