# Jarvis Cloud Migration Guide

This guide converts Jarvis from a Windows Local Core assistant into a cloud-first AI agent system.

## Direct Answer

Jarvis no longer needs `START_JARVIS.bat` for the main product path. The new primary architecture is:

```text
Vercel Next.js Frontend
  -> FastAPI Cloud Backend
  -> Agent Planner + LLM Provider
  -> Async Workers
  -> Playwright Chromium Sessions
  -> Supabase Auth, Realtime, and Postgres
```

The existing Windows Local Core is kept only as an optional hybrid connector for actions that truly require a user's laptop.

## Existing Local-Only Inventory

The legacy root app is centered around `main.py`, `www/`, and batch startup scripts.

Local-only dependencies found during migration:

- `START_JARVIS.bat` and `START_LOCAL_CORE.bat` start a Windows process manually.
- `main.py` imports and uses `ctypes`, `subprocess`, `webbrowser`, Eel, and `ThreadingHTTPServer`.
- Windows process launching is used for apps such as terminal, Calculator, Notepad, browser, and shutdown.
- Keyboard and mouse automation is implemented through Windows user32 calls.
- Local files are stored under `jarvis_data`.
- The old Vercel deployment served static `www/` plus Python API functions, while desktop actions still depended on the Local Core.

## New Folder Structure

```text
jarvis-main/
  frontend/        Next.js, TailwindCSS, shadcn-style UI, Supabase Auth
  backend/         FastAPI REST and WebSocket API
  agent/           Planner, policy, orchestration, LLM providers, browser tools
  workers/         Async worker and browser automation queue
  docker-compose.yml
  .env.example
  CLOUD_MIGRATION_GUIDE.md
```

## Frontend

The frontend is now a Next.js app in `frontend/`.

Main features:

- Vercel-compatible Next.js App Router
- TailwindCSS styling
- shadcn-style local components
- Supabase email/password and Google OAuth login
- Approval-first task cards
- Task history
- WebSocket-ready task streaming
- Responsive vertical sidebar

Run locally:

```bash
cd frontend
npm install
npm run dev
```

Set frontend environment values:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-public-anon-key
```

## Backend

The backend is now FastAPI in `backend/`.

Main routes:

- `GET /health`
- `POST /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/approve`
- `POST /api/tasks/{task_id}/cancel`
- `WS /ws/tasks/{task_id}`

Run locally:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

## Agent Layer

The new `agent/` package separates thinking from execution.

Core modules:

- `planner.py`: detects intent and creates execution plans.
- `policies.py`: forces approval for actionable tasks.
- `orchestrator.py`: runs plans and calls tools/providers.
- `providers.py`: supports OpenAI-compatible LLM providers with a local fallback.
- `tools/browser.py`: DDGS/DuckDuckGo, Playwright, and BeautifulSoup extraction paths.

Provider configuration:

```text
OPENAI_API_KEY=
OPENAI_BASE_URL=
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=qwen2.5-coder
```

Any OpenAI-compatible provider can be used: OpenAI, OpenRouter, LiteLLM, vLLM, Ollama through a gateway, or another compatible endpoint.

## Workers

The `workers/` folder provides async worker scaffolding for scalable execution.

Planned worker responsibilities:

- Run cloud Playwright sessions
- Extract content from pages
- Execute approved browser automation
- Stream progress to backend/Supabase
- Scale horizontally with Redis

Run with Docker Compose:

```bash
docker compose up --build
```

Services:

- `backend`: FastAPI API on port `8000`
- `worker`: browser automation worker
- `redis`: queue backend

## Supabase

Use Supabase for:

- Auth
- Google login
- user sessions
- Postgres task persistence
- Realtime streaming

Required public frontend variables:

```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

Required backend variables:

```text
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
```

Google login setup:

1. Enable Google provider in Supabase Auth.
2. Add your Vercel domain to allowed redirect URLs.
3. Add local dev URL if needed: `http://localhost:3000`.

## Deployment

### Frontend on Vercel

Recommended Vercel project settings:

- Framework: Next.js
- Root directory: `frontend`
- Build command: `npm run build`
- Output: Vercel auto-detects Next.js

This repo also includes a root `vercel.json` that points Vercel to `frontend/package.json` for the cloud app.

### Backend and Workers

Vercel is excellent for the frontend, but long-running Playwright workers should run in a Docker-capable host:

- Railway
- Render
- Fly.io
- AWS ECS
- Azure Container Apps
- Google Cloud Run
- a VPS with Docker

Deploy backend and workers from:

```text
backend/Dockerfile
workers/Dockerfile
docker-compose.yml
```

Set `NEXT_PUBLIC_API_BASE_URL` in Vercel to your deployed backend URL.

## Approval Workflow

All actionable tasks use this flow:

```text
User Prompt
  -> Intent Detection
  -> Task Planning
  -> Approval Request
  -> User Approves
  -> Worker Execution
  -> Completion Report
```

Approval is required for:

- sending email
- deployments
- file changes
- browser automation that changes state
- terminal/desktop connector requests
- external messaging

## Optional Hybrid Desktop Connector

Cloud Jarvis cannot directly control a private Windows laptop from Vercel. If desktop control is still needed, use the old Local Core as an optional connector:

```text
Vercel UI
  -> Cloud Backend
  -> Approval Card
  -> User-installed Desktop Connector
  -> Local app/file/system action
```

This connector is optional and not required for normal cloud mode.

## Migration Status

Completed in this migration:

- Added `frontend/` Next.js cloud app.
- Added `backend/` FastAPI API with REST and WebSocket endpoints.
- Added `agent/` modular planner/orchestrator/provider layer.
- Added `workers/` queue and worker scaffold.
- Added Dockerfiles and `docker-compose.yml`.
- Added `.env.example`.
- Updated Vercel config toward the cloud frontend.
- Documented Local Core as optional legacy/hybrid mode.

Recommended next steps:

1. Add persistent Supabase task tables.
2. Add backend auth middleware to validate Supabase JWTs.
3. Connect Redis queue from backend to workers.
4. Add full browser session recording and screenshots.
5. Add production observability and rate limits.
