import datetime
import concurrent.futures
import importlib.util
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


CODING_MODEL_ORDER = [
    "qwen2.5-coder:7b",
    "qwen2.5-coder",
    "deepseek-r1:7b",
    "deepseek-coder:6.7b",
    "codellama:7b",
    "starcoder2:7b",
]

REASONING_MODEL_ORDER = [
    "deepseek-r1:7b",
    "qwen2.5-coder:7b",
    "mistral:7b",
    "phi4",
    "gemma3",
]

GENERAL_MODEL_ORDER = [
    "qwen2.5-coder:7b",
    "deepseek-r1:7b",
    "mistral:7b",
    "phi4",
    "gemma3",
]


NEWS_FEEDS = [
    {"source": "BBC", "category": "World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "BBC", "category": "Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"source": "BBC", "category": "Technology", "url": "https://feeds.bbci.co.uk/news/technology/rss.xml"},
    {"source": "BBC", "category": "Science", "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
    {"source": "BBC", "category": "Sports", "url": "https://feeds.bbci.co.uk/sport/rss.xml"},
    {"source": "Al Jazeera", "category": "World", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"source": "NDTV", "category": "India", "url": "https://feeds.feedburner.com/ndtvnews-top-stories"},
    {"source": "NDTV", "category": "Business", "url": "https://feeds.feedburner.com/ndtvprofit-latest"},
    {"source": "Times of India", "category": "India", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
    {"source": "Times of India", "category": "Business", "url": "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms"},
    {"source": "The Hindu", "category": "India", "url": "https://www.thehindu.com/news/national/feeder/default.rss"},
    {"source": "CNBC", "category": "Business", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"source": "CNBC", "category": "Technology", "url": "https://www.cnbc.com/id/19854910/device/rss/rss.html"},
    {"source": "DW", "category": "World", "url": "https://rss.dw.com/rdf/rss-en-all"},
    {"source": "France24", "category": "World", "url": "https://www.france24.com/en/rss"},
    {"source": "NHK", "category": "World", "url": "https://www3.nhk.or.jp/rss/news/cat0.xml"},
]


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def optional_stack_status() -> dict:
    return {
        "ollama": bool(installed_ollama_models(timeout=0.7)),
        "pyautogui": module_available("pyautogui"),
        "pywin32": module_available("win32api") or module_available("win32gui"),
        "playwright": module_available("playwright"),
        "crawl4ai": module_available("crawl4ai"),
        "scrapy": module_available("scrapy"),
        "chromadb": module_available("chromadb"),
        "faiss": module_available("faiss"),
        "numpy": module_available("numpy"),
        "pandas": module_available("pandas"),
        "xgboost": module_available("xgboost"),
    }


def detect_intent(prompt: str) -> str:
    text = squash(prompt).lower()
    if re.search(r"\b(code|program|script|debug|bug|react|next|python|node|javascript|typescript|html|css|sql|java|c\+\+|cpp|website|app)\b", text):
        return "code"
    if re.search(r"\b(news|briefing|latest|today|current|world|business|sports|finance|market|ai|technology|india)\b", text):
        return "news"
    if re.search(r"\b(predict|prediction|forecast|trend|probability|risk|impact|likely|future)\b", text):
        return "prediction"
    if re.search(r"\b(email|message|whatsapp|draft|reply|send|share)\b", text):
        return "message"
    if re.search(r"\b(open|launch|terminal|command|scroll|shutdown|deploy|install|create file|edit file)\b", text):
        return "action"
    return "answer"


def installed_ollama_models(timeout: float = 1.5) -> list[str]:
    try:
        request = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []
    names = []
    for item in data.get("models", []):
        name = squash(item.get("name", ""))
        if name:
            names.append(name)
    return names


def choose_ollama_models(prompt: str, settings: dict | None = None) -> list[str]:
    settings = settings or {}
    intent = detect_intent(prompt)
    configured = squash(settings.get("ollama_model", ""))
    raw_fallbacks = settings.get("ollama_fallback_models", "")
    if isinstance(raw_fallbacks, list):
        configured_fallbacks = [squash(item) for item in raw_fallbacks if squash(item)]
    else:
        configured_fallbacks = [squash(item) for item in str(raw_fallbacks or "").split(",") if squash(item)]

    preferred = CODING_MODEL_ORDER if intent == "code" else REASONING_MODEL_ORDER if intent == "prediction" else GENERAL_MODEL_ORDER
    ordered = []
    for name in [configured, *configured_fallbacks, *preferred]:
        if name and name not in ordered:
            ordered.append(name)

    installed = installed_ollama_models()
    if not installed:
        return ordered[:4]

    installed_lower = {name.lower(): name for name in installed}
    usable = []
    for wanted in ordered:
        if wanted.lower() in installed_lower:
            usable.append(installed_lower[wanted.lower()])
            continue
        stem = wanted.split(":", 1)[0].lower()
        for model in installed:
            if model.lower().split(":", 1)[0] == stem and model not in usable:
                usable.append(model)
                break
    return usable or installed[:3]


def build_system_prompt(prompt: str, skill_context: str = "", extra_context: str = "") -> str:
    intent = detect_intent(prompt)
    base = [
        "You are Jarvis, a high-security local AI assistant.",
        "Answer directly first, then explain briefly, then give technical details only when useful.",
        "Correct obvious user typos silently.",
        "Never claim an external action happened unless a tool actually did it.",
        "Do not dump raw README markdown. Summarize long context into clear sections.",
        "Use concise paragraphs, clean bullet lists, and code fences only for code.",
    ]
    if intent == "code":
        base.extend(
            [
                "For coding tasks, produce complete runnable code, not placeholders.",
                "Infer the best language from the prompt and include file names or usage notes when useful.",
                "Prefer safe standard-library code unless a framework is requested.",
            ]
        )
    elif intent == "news":
        base.extend(
            [
                "For news, distinguish verified source facts from analysis.",
                "Mention uncertainty when live retrieval is limited.",
            ]
        )
    elif intent == "prediction":
        base.extend(
            [
                "For prediction, separate facts, assumptions, forecast, confidence, and risks.",
                "Use probabilities only as estimates, not guarantees.",
            ]
        )
    if skill_context:
        base.append("Active Jarvis skill rules:\n" + skill_context)
    if extra_context:
        base.append("Retrieved context:\n" + extra_context[:6000])
    return "\n".join(base)


def ollama_chat(prompt: str, settings: dict | None = None, skill_context: str = "", extra_context: str = "", timeout: float = 45) -> dict | None:
    models = choose_ollama_models(prompt, settings)
    if not models:
        return None
    system_prompt = build_system_prompt(prompt, skill_context=skill_context, extra_context=extra_context)
    errors = []
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.25 if detect_intent(prompt) == "code" else 0.35,
                "num_ctx": 8192,
            },
        }
        try:
            request = urllib.request.Request(
                "http://127.0.0.1:11434/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            started = time.time()
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = str(data.get("message", {}).get("content", "") or "").strip()
            if content:
                return {"model": model, "message": content, "seconds": round(time.time() - started, 2)}
        except Exception as error:
            errors.append(f"{model}: {error}")
            continue
    return {"model": "", "message": "", "errors": errors}


def _xml_text(node, names: list[str]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return squash(found.text)
    for child in list(node):
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag in {item.lower() for item in names} and child.text:
            return squash(child.text)
    return ""


def _parse_feed(raw: bytes, source: str, category: str, feed_url: str) -> list[dict]:
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []

    nodes = list(root.findall(".//item"))
    if not nodes:
        nodes = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() == "entry"]

    items = []
    for node in nodes[:12]:
        title = _xml_text(node, ["title"])
        summary = _xml_text(node, ["description", "summary", "content"])
        link = _xml_text(node, ["link"])
        if not link:
            for child in list(node):
                tag = child.tag.rsplit("}", 1)[-1].lower()
                if tag == "link":
                    link = child.attrib.get("href", "")
                    break
        published = _xml_text(node, ["pubDate", "published", "updated", "date"])
        if title:
            items.append(
                {
                    "title": title,
                    "summary": re.sub(r"<[^>]+>", " ", summary),
                    "link": squash(link),
                    "published": published,
                    "source": source,
                    "category": category,
                    "feed": feed_url,
                }
            )
    return items


def _wanted_categories(prompt: str) -> set[str]:
    text = squash(prompt).lower()
    wanted = set()
    mapping = {
        "Business": r"\b(business|finance|financial|market|markets|stock|stocks|economy|economic)\b",
        "Sports": r"\b(sport|sports|cricket|football|ipl|nba|tennis)\b",
        "Technology": r"\b(ai|artificial intelligence|technology|tech|startup|software|gadget|llm|deepseek|chatgpt)\b",
        "India": r"\b(india|indian|bharat|kiit|odisha)\b",
        "World": r"\b(world|global|international|geopolitics|war|election)\b",
        "Science": r"\b(science|space|research|health|medical|medicine)\b",
    }
    for category, pattern in mapping.items():
        if re.search(pattern, text):
            wanted.add(category)
    if not wanted:
        wanted.update({"World", "India", "Business", "Technology", "Sports"})
    return wanted


def collect_rss_news(prompt: str, max_items: int = 12, timeout: float = 2.5) -> list[dict]:
    wanted = _wanted_categories(prompt)
    query_tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", squash(prompt).lower())
        if len(token) > 2 and token not in {"latest", "today", "news", "briefing", "tell", "about"}
    }
    def fetch_one(feed: dict) -> list[dict]:
        try:
            request = urllib.request.Request(feed["url"], headers={"User-Agent": "JarvisNewsReader/1.0"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(1_000_000)
            return _parse_feed(raw, feed["source"], feed["category"], feed["url"])
        except Exception:
            return []

    items = []
    matching_feeds = [
        feed for feed in NEWS_FEEDS
        if feed["category"] in wanted or (feed["category"] == "Technology" and "AI" in wanted)
    ][:8]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, max(1, len(matching_feeds)))) as executor:
        futures = [executor.submit(fetch_one, feed) for feed in matching_feeds]
        try:
            completed = concurrent.futures.as_completed(futures, timeout=max(timeout + 1.0, 2.0))
            for future in completed:
                try:
                    items.extend(future.result(timeout=0))
                except Exception:
                    continue
        except concurrent.futures.TimeoutError:
            for future in futures:
                if future.done():
                    try:
                        items.extend(future.result(timeout=0))
                    except Exception:
                        continue

    seen = set()
    unique = []
    for item in items:
        key = (item.get("title", "").lower(), item.get("link", "").lower())
        if key in seen:
            continue
        seen.add(key)
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        score = sum(2 for token in query_tokens if token in text)
        if item.get("category") in wanted:
            score += 1
        item["score"] = score
        unique.append(item)
    unique.sort(key=lambda item: (item.get("score", 0), item.get("published", "")), reverse=True)
    return unique[:max_items]


def format_news_briefing(prompt: str, items: list[dict]) -> dict | None:
    if not items:
        return None
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    groups: dict[str, list[dict]] = {}
    for item in items:
        groups.setdefault(item.get("category") or "News", []).append(item)

    lines = [f"Latest briefing for {today}."]
    sections = []
    for category, category_items in list(groups.items())[:5]:
        lines.append("")
        lines.append(f"{category}:")
        section_items = []
        for item in category_items[:3]:
            title = squash(item.get("title", ""))
            summary = squash(item.get("summary", ""))
            source = squash(item.get("source", ""))
            link = squash(item.get("link", ""))
            published = squash(item.get("published", ""))
            short = summary[:220]
            suffix = f" ({source})" if source else ""
            detail = f": {short}" if short else ""
            source_link = f" Source: {link}" if link else ""
            lines.append(f"- {title}{suffix}{detail}{source_link}")
            section_items.append(
                {
                    "title": title,
                    "summary": short,
                    "source": source,
                    "link": link,
                    "published": published,
                }
            )
        sections.append({"name": category, "items": section_items, "provider": "RSS"})
    return {"message": "\n".join(lines), "sections": sections, "provider": "RSS"}


def prediction_report(prompt: str, evidence: list[dict] | None = None) -> str:
    topic = squash(re.sub(r"^(predict|forecast|analyze|what will happen with|trend)\s+", "", prompt, flags=re.IGNORECASE))
    topic = topic or squash(prompt)
    evidence = evidence or []
    facts = []
    for item in evidence[:4]:
        title = squash(item.get("title", ""))
        source = squash(item.get("source", ""))
        if title:
            facts.append(f"- {title}" + (f" ({source})" if source else ""))
    if not facts:
        facts.append("- No fresh external evidence was retrieved; this is a reasoning-only forecast.")

    return (
        f"Direct answer: I can analyze likely directions for {topic}, but this is a forecast, not a guarantee.\n\n"
        "Facts used:\n"
        + "\n".join(facts)
        + "\n\nForecast:\n"
        "- Near term: watch whether the newest signals repeat across multiple reliable sources.\n"
        "- Medium term: momentum is stronger when news, user demand, funding, and technical progress all point the same way.\n"
        "- Risk: one breaking event, regulation change, security issue, or market shock can reverse the trend.\n\n"
        "Confidence: medium when multiple recent sources agree; low when evidence is limited.\n\n"
        "Best next step: ask me for a live news check on this topic, then I can update the forecast with current sources."
    )


def detect_code_language(prompt: str) -> str:
    text = squash(prompt).lower()
    if re.search(r"\b(nextjs|next\.js|next)\b", text):
        return "tsx"
    if re.search(r"\breact\b", text):
        return "jsx"
    if re.search(r"\b(html|website|webpage|frontend|landing page)\b", text):
        return "html"
    for name in ["python", "javascript", "typescript", "java", "cpp", "c++", "csharp", "c#", "php", "sql"]:
        if name in text:
            return {"c++": "cpp", "c#": "csharp"}.get(name, name)
    return "python"


def title_from_prompt(prompt: str, fallback: str = "Smart Website") -> str:
    text = squash(prompt)
    text = re.sub(r"\b(write|create|generate|make|build|code|html|css|javascript|website|webpage|page|for|my|a|an|the)\b", " ", text, flags=re.IGNORECASE)
    words = [word for word in re.sub(r"[^a-zA-Z0-9 ]+", " ", text).split() if word][:5]
    if not words:
        return fallback
    return " ".join(word[:1].upper() + word[1:].lower() for word in words)


def html_preview_template(prompt: str) -> str:
    text = squash(prompt).lower()
    title = "Name Fixer" if "name fixer" in text else "Calculator" if "calculator" in text else "Task Manager" if re.search(r"\b(todo|task)\b", text) else title_from_prompt(prompt)
    is_name = "name fixer" in text
    is_calc = "calculator" in text
    is_task = re.search(r"\b(todo|task)\b", text) is not None

    if is_name:
        tool_markup = """
          <textarea id="nameInput" placeholder="Example:   md    WASI__portfolio site"></textarea>
          <div class="actions">
            <button id="runBtn">Fix name</button>
            <button id="copyBtn" class="secondary">Copy best</button>
          </div>
          <section id="results" class="results"></section>
        """
        script = """
      const input = document.querySelector("#nameInput");
      const results = document.querySelector("#results");
      function cleanWords(value) {
        return value.replace(/[_-]+/g, " ").replace(/[^a-zA-Z0-9 ]+/g, "").trim().split(/\\s+/).filter(Boolean);
      }
      function render() {
        const words = cleanWords(input.value);
        if (!words.length) {
          results.innerHTML = "<p>Type a name to fix it.</p>";
          return;
        }
        const display = words.map((word) => word[0].toUpperCase() + word.slice(1).toLowerCase()).join(" ");
        const username = words.map((word) => word.toLowerCase()).join("");
        const slug = words.map((word) => word.toLowerCase()).join("-");
        results.innerHTML = [
          ["Best display name", display],
          ["Username", username],
          ["Website slug", slug],
          ["Initials", words.map((word) => word[0].toUpperCase()).join("")]
        ].map(([label, value]) => `<article><span>${label}</span><strong>${value}</strong></article>`).join("");
      }
      document.querySelector("#runBtn").addEventListener("click", render);
      document.querySelector("#copyBtn").addEventListener("click", async () => {
        const best = results.querySelector("strong")?.textContent || "";
        if (best) await navigator.clipboard.writeText(best);
      });
      input.addEventListener("input", render);
      render();
        """
        subtitle = "Clean messy names into display names, usernames, slugs, and initials."
    elif is_calc:
        tool_markup = """
          <input id="display" value="0" readonly aria-label="Calculator display">
          <div id="keys" class="keys"></div>
        """
        script = """
      const keys = ["C", "(", ")", "/", "7", "8", "9", "*", "4", "5", "6", "-", "1", "2", "3", "+", "0", ".", "Back", "="];
      const display = document.querySelector("#display");
      document.querySelector("#keys").innerHTML = keys.map((key) => `<button class="${"+-*/=".includes(key) ? "op" : ""}">${key}</button>`).join("");
      document.querySelector("#keys").addEventListener("click", (event) => {
        const key = event.target.textContent;
        if (key === "C") display.value = "0";
        else if (key === "Back") display.value = display.value.slice(0, -1) || "0";
        else if (key === "=") display.value = /^[0-9+\\-*/(). ]+$/.test(display.value) ? String(Function("return " + display.value)()) : "Error";
        else display.value = display.value === "0" ? key : display.value + key;
      });
        """
        subtitle = "A polished browser calculator with safe expression validation."
    elif is_task:
        tool_markup = """
          <form id="taskForm" class="task-form">
            <input id="taskInput" placeholder="Add a task">
            <button>Add</button>
          </form>
          <ul id="taskList" class="task-list"></ul>
        """
        script = """
      const form = document.querySelector("#taskForm");
      const input = document.querySelector("#taskInput");
      const list = document.querySelector("#taskList");
      const tasks = ["Design UI", "Write code", "Test on mobile"];
      function render() {
        list.innerHTML = tasks.map((task, index) => `<li><button data-index="${index}">${task}</button></li>`).join("");
      }
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        if (input.value.trim()) tasks.push(input.value.trim());
        input.value = "";
        render();
      });
      list.addEventListener("click", (event) => event.target.closest("button")?.classList.toggle("done"));
      render();
        """
        subtitle = "Add, scan, and complete tasks in a clean responsive interface."
    else:
        tool_markup = """
          <div class="feature-grid">
            <article><span>01</span><strong>Clear Layout</strong><p>Readable sections with strong hierarchy and mobile spacing.</p></article>
            <article><span>02</span><strong>Real Controls</strong><p>Buttons, cards, and inputs feel like a working product.</p></article>
            <article><span>03</span><strong>Responsive</strong><p>The page adapts cleanly from phone to desktop.</p></article>
          </div>
          <button id="actionBtn">Try interaction</button>
          <p id="status" class="status">Ready.</p>
        """
        script = """
      document.querySelector("#actionBtn").addEventListener("click", () => {
        document.querySelector("#status").textContent = "Interaction working. Replace this with your app logic.";
      });
        """
        subtitle = f"A polished responsive {title} page generated from your prompt."

    return f"""```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #111827;
        background:
          radial-gradient(circle at top left, rgba(20, 184, 166, .18), transparent 32rem),
          linear-gradient(135deg, #f8fafc, #eef2f7);
      }}
      main {{ width: min(980px, 100%); display: grid; gap: 18px; }}
      .hero {{
        display: grid;
        gap: 20px;
        padding: clamp(22px, 5vw, 48px);
        border: 1px solid #dbe3ec;
        border-radius: 18px;
        background: rgba(255, 255, 255, .92);
        box-shadow: 0 24px 70px rgba(15, 23, 42, .12);
      }}
      .eyebrow {{ margin: 0; color: #0f766e; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; font-size: .8rem; }}
      h1 {{ margin: 0; font-size: clamp(2.4rem, 8vw, 5rem); line-height: .95; letter-spacing: 0; }}
      .lead {{ max-width: 720px; margin: 0; color: #5b6472; font-size: clamp(1rem, 2vw, 1.2rem); line-height: 1.65; }}
      textarea, input {{
        width: 100%;
        min-height: 48px;
        padding: 13px 14px;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        background: #fff;
        font: inherit;
      }}
      textarea {{ min-height: 128px; resize: vertical; }}
      button {{
        min-height: 44px;
        padding: 11px 15px;
        border: 0;
        border-radius: 12px;
        background: #0f766e;
        color: white;
        font-weight: 800;
        cursor: pointer;
      }}
      button.secondary {{ color: #111827; background: #e5e7eb; }}
      .actions, .task-form {{ display: flex; flex-wrap: wrap; gap: 10px; }}
      .task-form input {{ flex: 1 1 220px; }}
      .feature-grid, .results, .task-list {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        padding: 0;
        list-style: none;
      }}
      article, li button, .status {{
        width: 100%;
        display: grid;
        gap: 6px;
        padding: 16px;
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        background: #f8fafc;
        text-align: left;
      }}
      article span {{ color: #64748b; font-size: .82rem; font-weight: 800; }}
      article strong {{ font-size: 1.05rem; overflow-wrap: anywhere; }}
      article p, .status {{ margin: 0; color: #667085; line-height: 1.5; }}
      .keys {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
      .keys button {{ background: #e5e7eb; color: #111827; }}
      .keys .op {{ background: #0f766e; color: #fff; }}
      .done {{ text-decoration: line-through; opacity: .5; }}
      @media (max-width: 620px) {{
        body {{ padding: 14px; }}
        .hero {{ border-radius: 14px; }}
        .feature-grid, .results, .task-list {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">Preview ready</p>
        <h1>{title}</h1>
        <p class="lead">{subtitle}</p>
        {tool_markup}
      </section>
    </main>
    <script>
{script}
    </script>
  </body>
</html>
```"""


def cloud_code_response(prompt: str) -> str:
    language = detect_code_language(prompt)
    text = squash(prompt).lower()
    title = title_from_prompt(prompt, fallback="Generated App")
    if language == "python" and "calculator" in text:
        return """```python
def calculate(expression: str) -> float:
    allowed = set("0123456789+-*/(). ")
    if not expression or any(char not in allowed for char in expression):
        raise ValueError("Expression contains unsupported characters.")
    return eval(expression, {"__builtins__": {}}, {})


def main() -> None:
    print("Calculator")
    while True:
        expression = input("Enter expression or q to quit: ").strip()
        if expression.lower() in {"q", "quit", "exit"}:
            break
        try:
            print(calculate(expression))
        except Exception as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
```"""
    if language == "html":
        return html_preview_template(prompt)
    if language in {"jsx", "tsx"}:
        fence = "tsx" if language == "tsx" else "jsx"
        prelude = '"use client";\n\n' if language == "tsx" else ""
        component = re.sub(r"[^a-zA-Z0-9]+", " ", title).title().replace(" ", "") or "GeneratedApp"
        return f"""```{fence}
{prelude}import {{ useMemo, useState }} from "react";

export default function {component}() {{
  const [value, setValue] = useState("");
  const cleaned = useMemo(() => value.trim().replace(/\\s+/g, " "), [value]);

  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 p-6 text-slate-950">
      <section className="grid w-full max-w-3xl gap-5 rounded-2xl bg-white p-6 shadow-xl">
        <header>
          <p className="text-sm font-bold uppercase tracking-wide text-teal-700">Preview ready</p>
          <h1 className="text-4xl font-black md:text-6xl">{title}</h1>
          <p className="text-slate-500">A responsive React interface generated from your prompt.</p>
        </header>
        <textarea
          className="min-h-32 rounded-xl border p-4"
          value={{value}}
          onChange={{(event) => setValue(event.target.value)}}
          placeholder="Type something to test the UI"
        />
        <article className="rounded-xl bg-slate-50 p-4">
          <strong>Output</strong>
          <p>{{cleaned || "Waiting for input..."}}</p>
        </article>
      </section>
    </main>
  );
}}
```"""
    if language == "python":
        return f'''```python
def clean_text(value: str) -> str:
    """Normalize spacing in user-provided text."""
    return " ".join(value.strip().split())


def main() -> None:
    print("{title}")
    raw = input("Enter text: ")
    print("Result:", clean_text(raw))


if __name__ == "__main__":
    main()
```'''
    if language in {"javascript", "typescript"}:
        type_text = ": string" if language == "typescript" else ""
        return f'''```{language}
function cleanText(value{type_text}){": string" if language == "typescript" else ""} {{
  return value.trim().replace(/\\s+/g, " ");
}}

function main() {{
  const result = cleanText("  Example input for {title}  ");
  console.log(result);
}}

main();
```'''
    return (
        f"```python\n"
        f"def main() -> None:\n"
        f"    print(\"{title}\")\n\n"
        f"if __name__ == \"__main__\":\n"
        f"    main()\n"
        f"```"
    )
