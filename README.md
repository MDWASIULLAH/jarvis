# Jarvis

Jarvis is a local-first AI command center with a Vercel-ready web UI.

It is built to behave like an approval-first autonomous assistant: Jarvis understands a natural-language task, plans the safest execution path, asks permission in the web UI, then continues the workflow through the Local Core connector.

## Features

- Natural-language task planning
- Approval cards for actionable tasks
- Local desktop app opening through the Local Core connector
- Email and sharing drafts with permission
- Free DDGS/SearXNG-ready search stack
- Local RAG memory and skill packs
- Coding assistant defaults for Ollama + Qwen2.5-Coder
- Vercel-ready web UI and Python planner API
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
