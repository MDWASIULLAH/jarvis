import json
import re
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import sys
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_agent import plan_task  # noqa: E402
from jarvis_intelligence import cloud_code_response, collect_rss_news, format_news_briefing  # noqa: E402


def _squash(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_query(prompt: str) -> str:
    query = re.sub(r"^(search|google|find|look up)\s+", "", prompt, flags=re.IGNORECASE).strip()
    query = re.sub(r"\b(tell me|give me|show me|latest|today|current)\b", " ", query, flags=re.IGNORECASE)
    query = _squash(query)
    return query or prompt


def _is_identity(prompt: str) -> bool:
    normalized = _squash(prompt).lower().replace("what's", "whats")
    return normalized in {
        "whats your name",
        "what is your name",
        "your name",
        "who are you",
        "what are you",
    }


def _normalize_results(raw_results: list[dict], provider: str) -> list[dict]:
    results = []
    seen = set()
    for item in raw_results:
        title = _squash(item.get("title") or item.get("source") or "Search result")
        url = _squash(item.get("href") or item.get("url") or item.get("link") or "")
        content = _squash(item.get("body") or item.get("content") or item.get("snippet") or "")
        if not title and not content:
            continue
        key = (title.lower(), url)
        if key in seen:
            continue
        seen.add(key)
        results.append({"title": title, "url": url, "content": content, "provider": provider})
    return results[:5]


def _ddgs_search(query: str, news: bool = False) -> list[dict]:
    try:
        try:
            from ddgs import DDGS
        except Exception:
            from duckduckgo_search import DDGS
    except Exception:
        return []

    try:
        with DDGS() as ddgs:
            if news and hasattr(ddgs, "news"):
                raw = list(ddgs.news(query, region="in-en", safesearch="moderate", timelimit="d", max_results=5))
            else:
                raw = list(ddgs.text(query, region="in-en", safesearch="moderate", max_results=5))
        return _normalize_results(raw, "DDGS")
    except TypeError:
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=5))
            return _normalize_results(raw, "DDGS")
        except Exception:
            return []
    except Exception:
        return []


def _duckduckgo_html_search(query: str) -> list[dict]:
    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "JarvisCloudAgent/1.0"})
        with urllib.request.urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", "ignore")
    except Exception:
        return []

    try:
        from bs4 import BeautifulSoup
    except Exception:
        return []

    soup = BeautifulSoup(html, "html.parser")
    raw = []
    for result in soup.select(".result")[:5]:
        link = result.select_one(".result__title a") or result.select_one("a.result__a")
        snippet = result.select_one(".result__snippet") or result.select_one(".result__body")
        if not link:
            continue
        raw.append(
            {
                "title": link.get_text(" ", strip=True),
                "href": link.get("href", ""),
                "body": snippet.get_text(" ", strip=True) if snippet else "",
            }
        )
    return _normalize_results(raw, "DuckDuckGo HTML")


def _format_search_answer(prompt: str, results: list[dict]) -> str:
    if not results:
        return (
            "I could not fetch live web results from the free cloud search stack right now.\n\n"
            "Try again in a moment, or connect Local Core for DDGS/SearXNG plus local scraping."
        )

    lead = f"Here is what I found for {_clean_query(prompt)}."
    points = []
    for item in results[:3]:
        title = _squash(item.get("title", "Result"))
        content = _squash(item.get("content", ""))
        points.append(f"- {title}: {content}" if content else f"- {title}")

    sources = ["Sources:"]
    for index, item in enumerate(results[:5], start=1):
        url = item.get("url") or ""
        title = item.get("title") or "Source"
        if url:
            sources.append(f"{index}. {title} - {url}")

    return "\n\n".join([lead, "Key points:\n" + "\n".join(points), "\n".join(sources)])


def _cloud_code_answer(prompt: str) -> dict | None:
    if not re.search(r"\b(write|create|generate|make|build|fix|debug)\b", prompt, re.IGNORECASE):
        return None
    if not re.search(r"\b(code|program|script|python|javascript|typescript|html|css|react|next|website|app|calculator)\b", prompt, re.IGNORECASE):
        return None
    return {
        "type": "code",
        "message": cloud_code_response(prompt),
    }


def _web_answer(prompt: str, intent: str) -> dict | None:
    if _is_identity(prompt):
        return {
            "type": "answer",
            "message": "My name is Jarvis.\n\nI am your web and desktop AI assistant. On Vercel I can answer, plan, draft, and ask approval. With Local Core connected, I can also control apps on your laptop.",
        }

    news = bool(re.search(r"\b(news|briefing|latest|today|current|business|sports|ai|technology)\b", prompt, re.IGNORECASE))
    searchable = intent in {"research", "answer"} and (
        news
        or re.search(r"\b(tell me about|what is|who is|where is|explain|describe|information about|details about)\b", prompt, re.IGNORECASE)
    )
    if not searchable:
        return None

    query = _clean_query(prompt)
    results = _ddgs_search(query, news=news) or _duckduckgo_html_search(query)
    if news and not results:
        briefing = format_news_briefing(prompt, collect_rss_news(prompt, timeout=1.5))
        if briefing:
            return {
                "type": "briefing",
                "message": briefing["message"],
                "briefing": briefing,
            }
    message = _format_search_answer(prompt, results)
    return {
        "type": "briefing" if news else "answer",
        "message": message,
        "briefing": {"message": message, "sections": []} if news else None,
    }


class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        prompt = str(data.get("command") or data.get("prompt") or "").strip()
        if not prompt:
            self._send(400, {"type": "error", "message": "Missing prompt."})
            return

        plan = plan_task(prompt)
        code_answer = _cloud_code_answer(prompt)
        if code_answer:
            self._send(200, code_answer)
            return

        web_answer = _web_answer(prompt, plan.get("intent", "answer"))
        if web_answer:
            self._send(200, web_answer)
            return

        if plan.get("approval_required"):
            self._send(
                200,
                {
                    "type": "confirm_action",
                    "action": "agent_workflow",
                    "browserOnly": True,
                    "message": "Jarvis prepared a safe execution plan. Approve here to continue; desktop-only steps need the optional Local Core connector.",
                    "plan": plan,
                },
            )
            return

        self._send(
            200,
            {
                "type": "answer",
                "message": "Jarvis Cloud Agent is online.\n\nAsk a question, request code, search news, or approve an action. Desktop app control needs the optional Local Core connector because browsers cannot privately control Windows apps from Vercel.",
                "plan": plan,
            },
        )
