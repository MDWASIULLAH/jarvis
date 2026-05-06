# Jarvis

Jarvis is being migrated into a cloud-first AI agent system with a Vercel Next.js frontend, FastAPI backend, Supabase auth, and scalable browser automation workers.

The legacy Windows Local Core still exists for optional hybrid desktop control, but the main cloud product no longer depends on manually running `START_JARVIS.bat`.

## Features

- Natural-language task planning
- Approval cards for actionable tasks
- Cloud browser automation architecture with Playwright workers
- Email and sharing drafts with permission
- Free DDGS/SearXNG-ready search stack
- Local RAG memory and skill packs
- Coding assistant defaults for Ollama + Qwen2.5-Coder
- Next.js frontend for Vercel
- FastAPI backend with REST and WebSocket routes
- Login/sign-up UI with Supabase Google OAuth support
- Mobile responsive sidebar and chat interface

## Architecture

```
Vercel Next.js Frontend
  -> FastAPI Backend
  -> Jarvis Agent Planner
  -> Approval Workflow
  -> Async Workers
  -> Playwright Cloud Browser Sessions
  -> Completion Report
```

The Vercel app hosts the web UI. The backend and workers run as Docker services on a container host. Desktop actions such as opening VS Code on a user's private laptop require the optional hybrid connector because Vercel cannot directly control a local Windows desktop.

## Running Jarvis in Cloud Mode

Cloud mode is the primary architecture.

1. Copy environment values:

```bat
copy .env.example .env
copy frontend\env.example frontend\.env.local
```

2. Start backend, worker, and Redis:

```bat
docker compose up --build
```

3. Start the frontend:

```bat
cd frontend
npm install
npm run dev
```

4. Open:

```text
http://localhost:3000
```

The frontend talks to the backend using:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

For production, deploy `frontend/` to Vercel and deploy `backend/` plus `workers/` to a Docker-capable host.

## Authentication

Jarvis includes a Supabase Auth sign-in screen:

- email sign-in/sign-up with `supabase.auth.signInWithPassword` and `supabase.auth.signUp`
- Google sign-in with `supabase.auth.signInWithOAuth({ provider: "google" })`
- browser session restore through the Supabase client

Set these public Supabase variables in Vercel, `.env`, or `.env.local`:

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-public-anon-or-publishable-key
```

These aliases are also supported:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_PUBLISHABLE_KEY
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
```

To enable Google login, turn on the Google provider in Supabase Auth and add your local and Vercel URLs to the Supabase redirect allow list:

```text
http://127.0.0.1:8765/index.html
https://jarvisj1.vercel.app/index.html
```

## Legacy Local Core

The old Windows Local Core is now optional legacy/hybrid mode. Use it only when you need direct laptop control.

```bat
START_JARVIS.bat
```

Then open:

```text
http://127.0.0.1:8765/index.html
```

## Install Dependencies

```bat
pip install -r requirements.txt
```

Optional local coding model setup:

```bat
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:7b
```

## Vercel Frontend

This repo includes:

- `frontend/` for the Next.js app
- `frontend/vercel.json` for frontend deployment
- root `vercel.json` pointing Vercel to `frontend/package.json`

Recommended Vercel setting:

```text
Root Directory: frontend
```

Set `NEXT_PUBLIC_API_BASE_URL` to the deployed FastAPI backend URL.

## Cloud Backend

FastAPI routes:

- `GET /health`
- `POST /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/approve`
- `POST /api/tasks/{task_id}/cancel`
- `WS /ws/tasks/{task_id}`

See `CLOUD_MIGRATION_GUIDE.md` for the full migration details.

Legacy deployment command:

```bat
vercel deploy
```

## Free Search Stack

Jarvis uses free/open-source search and scraping fallbacks:

- DDGS / DuckDuckGo Search
- Optional SearXNG
- requests + BeautifulSoup
- optional Crawl4AI / Playwright when installed locally

## Recommended Local Coding Models

Jarvis is configured to prefer Ollama with Qwen2.5-Coder locally:

```bat
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:7b
```

Qwen2.5-Coder is the primary coding model. DeepSeek R1, Phi, Mistral, Gemma, or other Ollama models can be used as fallback by changing `ollama_model` in local settings.

## Security

Jarvis keeps high-security defaults:

- approval cards for actions
- backend-only key handling
- no frontend API keys
- confirmation before email, sharing, terminal, shutdown, desktop automation, and agent workflows

## License

This project is released under the MIT License. See `LICENSE`.
