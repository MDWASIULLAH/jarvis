# Jarvis

Jarvis is a local-first AI command center with a Vercel-ready web UI.

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

## Vercel

This repo includes:

- `vercel.json` for static UI + Python API routing
- `api/agent.py` for task planning
- `www/` for the web interface
- `main.py` for the desktop Local Core connector

On Vercel, desktop execution is delegated back to the Local Core connector after user approval in the UI.

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
