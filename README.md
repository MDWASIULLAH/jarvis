# Jarvis

Jarvis is a local-first AI command center with a Vercel-ready web UI.

It is built to behave like an approval-first autonomous assistant: Jarvis understands a natural-language task, plans the safest execution path, asks permission in the web UI, then continues the workflow through the Local Core connector.

## Features

- Natural-language task planning
- Approval cards for actionable tasks
- Local desktop app opening through the Local Core connector
- Email and sharing drafts with permission
- Free DDGS/SearXNG-ready search stack
- RSS-backed live news fallback for global and India news
- Local RAG memory and skill packs
- Multi-model Ollama routing for Qwen2.5-Coder, DeepSeek, CodeLlama, StarCoder2, Mistral, Phi, and Gemma
- Prediction and risk-analysis responses that separate facts from forecasts
- Vercel-ready web UI and Python planner API
- Cloud web mode that does not require localhost for web-safe tasks
- Login/sign-up UI with Google Identity Services support
- Mobile responsive sidebar and chat interface

## Architecture

```
User Prompt
  -> Intent Detection
  -> Task Planning
  -> Approval Request
  -> Local Core / Web API Execution
  -> Completion Report
```

The Vercel app can host the UI and planning API. Desktop actions such as opening VS Code, running terminal commands, scrolling YouTube, editing local files, or sending messages from the laptop require the Local Core connector because Vercel cannot control a user's Windows desktop directly.

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

## Run Locally

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

Optional advanced local tools:

```bat
pip install -r requirements-optional.txt
python -m playwright install chromium
```

Optional local coding model setup:

```bat
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:7b
```

## Vercel

This repo includes:

- `vercel.json` for static UI + Python API routing
- `api/agent.py` for task planning
- `www/` for the web interface
- `main.py` for the desktop Local Core connector

On Vercel, desktop execution is delegated back to the Local Core connector after user approval in the UI.

Deploy with:

```bat
vercel deploy
```

Or connect this GitHub repository to Vercel for automatic deployments.

## Free Search Stack

Jarvis uses free/open-source search and scraping fallbacks:

- DDGS / DuckDuckGo Search
- Optional SearXNG
- requests + BeautifulSoup
- optional Crawl4AI / Playwright when installed locally

## Recommended Local Coding Models

Jarvis is configured to prefer Ollama with Qwen2.5-Coder locally, then fall back through DeepSeek, CodeLlama, StarCoder2, Mistral, Phi, or Gemma when those models are installed:

```bat
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:7b
ollama pull deepseek-coder:6.7b
ollama pull codellama:7b
ollama pull starcoder2:7b
```

Qwen2.5-Coder is the primary coding model. DeepSeek R1 is preferred for reasoning and prediction. Jarvis checks installed Ollama models and chooses the best available local model for the prompt.

## Advanced Intelligence Layer

`jarvis_intelligence.py` adds modular intelligence without replacing the current UI or local core:

- coding model routing through Ollama
- direct-answer-first system prompts
- RSS news ingestion from sources such as BBC, Al Jazeera, NDTV, Times of India, The Hindu, CNBC, DW, France24, and NHK
- prediction reports with facts, assumptions, confidence, and risks
- optional stack detection for Playwright, Crawl4AI, Scrapy, pyautogui, pywin32, ChromaDB, FAISS, NumPy, Pandas, and XGBoost

The default flow is:

```text
User Prompt
  -> Intent Router
  -> RAG / Search / News / Model Router
  -> Jarvis Answer or Approval Card
  -> Local Core Execution after approval
```

## Live News

Jarvis first tries DDGS/SearXNG for live search. If those return no results, it falls back to RSS feeds and formats clean category briefings with source links. Example prompts:

```text
business news
latest AI news
sports news today
predict the AI trend this week
```

## Security

Jarvis keeps high-security defaults:

- approval cards for actions
- backend-only key handling
- no frontend API keys
- confirmation before email, sharing, terminal, shutdown, desktop automation, and agent workflows

## License

This project is released under the MIT License. See `LICENSE`.
