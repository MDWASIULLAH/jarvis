import datetime
import json
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "jarvis_data"
SKILL_DIR = DATA_DIR / "brain" / "skills"
SKILLS_FILE = SKILL_DIR / "skills.json"


DEFAULT_SKILLS = [
    {
        "id": "answer_router",
        "title": "Answer Router",
        "category": "answering",
        "intent": "answer",
        "triggers": ["answer", "question", "what", "who", "where", "why", "how", "explain", "about"],
        "examples": [
            "tell me about KIIT University",
            "what is machine learning",
            "explain photosynthesis",
            "who is Nikola Tesla",
        ],
        "text": (
            "Decide whether the user needs a direct answer, live retrieval, RAG memory, code, or desktop action. "
            "For factual questions, correct typos, gather context first, answer in clear paragraphs, and avoid the command-help fallback."
        ),
    },
    {
        "id": "coding_architect",
        "title": "Coding Architect",
        "category": "coding",
        "intent": "code",
        "triggers": ["code", "program", "python", "javascript", "typescript", "java", "cpp", "csharp", "php", "sql"],
        "examples": [
            "write python code for a calculator",
            "create javascript code for a todo app",
            "write java code for name fixer",
            "make sql for users table",
        ],
        "text": (
            "When the user asks for code, infer the best language from the prompt. Produce complete runnable code, not unfinished placeholders. "
            "Include validation, clean naming, helpful structure, and a short usage note when useful."
        ),
    },
    {
        "id": "model_router",
        "title": "Model Router",
        "category": "reasoning",
        "intent": "answer",
        "triggers": ["ollama", "qwen", "deepseek", "codellama", "starcoder", "model", "reason"],
        "examples": [
            "write production code with the best local model",
            "reason deeply about this bug",
            "use coding model",
        ],
        "text": (
            "Route coding work to Qwen2.5-Coder first, then DeepSeek or other local models. "
            "Use reasoning models for analysis, risk, prediction, and planning. Fall back gracefully when a model is not installed."
        ),
    },
    {
        "id": "frontend_builder",
        "title": "Frontend Builder",
        "category": "coding",
        "intent": "code",
        "triggers": ["html", "css", "website", "webpage", "react", "nextjs", "frontend", "preview", "responsive"],
        "examples": [
            "make html css javascript website for name fixer",
            "create react dashboard",
            "make nextjs landing page",
            "preview the website",
        ],
        "text": (
            "For websites and apps, output complete preview-ready HTML, React, or Next.js code. Keep it responsive, mobile friendly, "
            "with real controls, polished spacing, accessible labels, and no fake unfinished sections."
        ),
    },
    {
        "id": "python_builder",
        "title": "Python Builder",
        "category": "coding",
        "intent": "code",
        "triggers": ["python", "tkinter", "cli", "script", "automation", "calculator"],
        "examples": [
            "write python tkinter calculator",
            "create python file organizer",
            "make python script to rename files",
        ],
        "text": (
            "For Python, prefer simple standard library solutions first. Use functions/classes when they clarify the task. "
            "Avoid unsafe eval unless tightly restricted. Include an if __name__ == '__main__' entry point for runnable scripts."
        ),
    },
    {
        "id": "message_writer",
        "title": "Message And Email Writer",
        "category": "communication",
        "intent": "email_draft",
        "triggers": ["email", "message", "whatsapp", "send", "share", "draft", "reply", "letter"],
        "examples": [
            "draft email to teacher for leave",
            "write whatsapp message about meeting",
            "send a professional job inquiry email",
        ],
        "text": (
            "Write full useful messages, not one-line drafts. Include subject when email is requested, greeting, clear body, next step, and closing. "
            "Before sending email, WhatsApp, or sharing to any app, ask for approval and show the final text."
        ),
    },
    {
        "id": "news_briefing",
        "title": "News Briefing",
        "category": "research",
        "intent": "news",
        "triggers": ["news", "briefing", "business", "sports", "ai", "technology", "world", "india", "science"],
        "examples": [
            "business news",
            "sports news",
            "ai news today",
            "latest technology news",
        ],
        "text": (
            "For news, route to live retrieval and organize results by requested category. Mention the date, keep sections short, "
            "and do not invent breaking news when retrieval fails."
        ),
    },
    {
        "id": "news_analyst",
        "title": "Live News Analyst",
        "category": "research",
        "intent": "news",
        "triggers": ["breaking", "reuters", "bbc", "al jazeera", "cnbc", "world events", "sources"],
        "examples": [
            "compare today's AI news sources",
            "give me business news with sources",
            "summarize world events today",
        ],
        "text": (
            "Use RSS, DDGS, SearXNG, and article extraction before answering live-news prompts. "
            "Group news by category, include source names and links, summarize first, and avoid unsupported claims."
        ),
    },
    {
        "id": "prediction_reasoner",
        "title": "Prediction Reasoner",
        "category": "reasoning",
        "intent": "prediction",
        "triggers": ["predict", "forecast", "trend", "probability", "risk", "future impact"],
        "examples": [
            "predict the AI trend this month",
            "forecast market risk from these news items",
            "what is likely to happen next",
        ],
        "text": (
            "Separate facts from forecasts. Give assumptions, likely scenarios, confidence, risk factors, and signals to watch. "
            "Never present predictions as certain facts."
        ),
    },
    {
        "id": "desktop_operator",
        "title": "Desktop Operator",
        "category": "actions",
        "intent": "open",
        "triggers": ["open", "launch", "start", "app", "calculator", "notepad", "youtube", "scroll", "terminal"],
        "examples": [
            "open calculator",
            "open youtube shorts and scroll",
            "run terminal dir",
        ],
        "text": (
            "For desktop actions, parse the safe target instead of running raw user text. Open known apps and websites directly. "
            "Ask approval before terminal, shutdown, sharing, or repeated automation."
        ),
    },
    {
        "id": "autonomous_executor",
        "title": "Autonomous Executor",
        "category": "actions",
        "intent": "open",
        "triggers": ["agent", "workflow", "execute", "do task", "continue", "approve", "autonomous"],
        "examples": [
            "create a project then run it",
            "open youtube shorts and keep scrolling",
            "after approval continue the workflow",
        ],
        "text": (
            "For multi-step tasks, create a short plan, ask approval for risky steps, then continue automatically after approval. "
            "Report progress and failures clearly without pretending blocked actions succeeded."
        ),
    },
    {
        "id": "security_guard",
        "title": "Security Guard",
        "category": "security",
        "intent": "security",
        "triggers": ["security", "permission", "approve", "send", "share", "terminal", "shutdown", "delete"],
        "examples": [
            "send email to Alex",
            "share news to WhatsApp",
            "run terminal command",
            "shutdown computer",
        ],
        "text": (
            "Security is high priority. Sensitive actions require approval. Never send, share, shut down, or run terminal commands silently. "
            "Never claim an action happened unless the app or backend actually did it."
        ),
    },
    {
        "id": "rag_researcher",
        "title": "RAG Researcher",
        "category": "research",
        "intent": "training",
        "triggers": ["rag", "dataset", "kaggle", "github", "link", "learn", "train", "knowledge"],
        "examples": [
            "train from dataset mydata.csv",
            "add link https://github.com/example/repo",
            "learn knowledge title CSS text responsive layout rules",
        ],
        "text": (
            "Use RAG for documents, links, GitHub READMEs, datasets, and user-provided lessons. Save readable text into memory, "
            "retrieve matching context before answering, and name sources when available."
        ),
    },
    {
        "id": "conversation_repair",
        "title": "Conversation Repair",
        "category": "conversation",
        "intent": "chat",
        "triggers": ["continue", "rewrite", "wrong", "spelling", "typo", "improve", "again", "better"],
        "examples": [
            "continue",
            "rewrite it better",
            "i wrote spelling wrong still understand",
        ],
        "text": (
            "Correct obvious spelling mistakes and keep context from the last generated answer. If the user says continue, improve, rewrite, "
            "or does not like it, continue the previous task instead of resetting."
        ),
    },
]


def _ensure_dirs() -> None:
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    if not SKILLS_FILE.exists():
        SKILLS_FILE.write_text("[]", encoding="utf-8")


def _load_skills() -> list[dict]:
    _ensure_dirs()
    try:
        data = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_skills(skills: list[dict]) -> None:
    _ensure_dirs()
    SKILLS_FILE.write_text(json.dumps(skills, indent=2, ensure_ascii=False), encoding="utf-8")


def _skill_text(skill: dict) -> str:
    examples = "; ".join(skill.get("examples", [])[:4])
    triggers = ", ".join(skill.get("triggers", [])[:10])
    return (
        f"Skill: {skill.get('title', skill.get('id', 'skill'))}\n"
        f"Category: {skill.get('category', 'general')}\n"
        f"Intent: {skill.get('intent', 'chat')}\n"
        f"Triggers: {triggers}\n"
        f"Examples: {examples}\n"
        f"Rules: {skill.get('text', '')}"
    )


def install_default_skills(add_knowledge=None, add_intent_example=None, force: bool = False) -> dict:
    existing = _load_skills()
    by_id = {skill.get("id"): skill for skill in existing if skill.get("id")}
    installed = []
    refreshed = []
    updated = []

    for skill in DEFAULT_SKILLS:
        skill_id = skill["id"]
        should_write = force or skill_id not in by_id
        if should_write:
            stored = dict(skill)
            stored["installed_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            by_id[skill_id] = stored
            installed.append(skill_id)
            if add_knowledge:
                add_knowledge(stored["title"], _skill_text(stored), f"jarvis-skill:{skill_id}")
            if add_intent_example:
                for example in stored.get("examples", []):
                    add_intent_example(example, stored.get("intent", "chat"))
        else:
            current = by_id[skill_id]
            changed = any(current.get(key) != skill.get(key) for key in ["title", "category", "intent", "triggers", "examples", "text"])
            if changed:
                stored = dict(skill)
                stored["installed_at"] = current.get("installed_at") or datetime.datetime.now().isoformat(timespec="seconds")
                stored["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
                by_id[skill_id] = stored
                updated.append(skill_id)
                if add_knowledge:
                    add_knowledge(stored["title"], _skill_text(stored), f"jarvis-skill:{skill_id}")
            else:
                refreshed.append(skill_id)

    ordered = [by_id[skill["id"]] for skill in DEFAULT_SKILLS]
    extras = [skill for skill in existing if skill.get("id") not in {item["id"] for item in DEFAULT_SKILLS}]
    _save_skills(ordered + extras)
    return {
        "installed": len(installed),
        "updated": len(updated),
        "existing": len(refreshed),
        "total": len(ordered) + len(extras),
        "ids": installed + updated,
    }


def skill_status() -> dict:
    skills = _load_skills()
    if not skills:
        return {"total": 0, "categories": {}, "skills": []}
    categories = Counter(skill.get("category", "general") for skill in skills)
    return {
        "total": len(skills),
        "categories": dict(sorted(categories.items())),
        "skills": [
            {
                "id": skill.get("id", ""),
                "title": skill.get("title", ""),
                "category": skill.get("category", ""),
            }
            for skill in skills
        ],
    }


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", (text or "").lower()))


def matching_skills(command: str, limit: int = 3) -> list[dict]:
    skills = _load_skills() or DEFAULT_SKILLS
    query = _tokens(command)
    if not query:
        return []

    scored = []
    for skill in skills:
        trigger_tokens = _tokens(" ".join(skill.get("triggers", [])))
        title_tokens = _tokens(skill.get("title", ""))
        example_tokens = _tokens(" ".join(skill.get("examples", [])))
        text_tokens = _tokens(skill.get("text", ""))
        score = 0
        score += 5 * len(query & trigger_tokens)
        score += 3 * len(query & title_tokens)
        score += 2 * len(query & example_tokens)
        score += len(query & text_tokens)
        if score > 0:
            scored.append((score, skill))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [skill for _, skill in scored[:limit]]


def skill_context(command: str, limit: int = 2) -> str:
    matches = matching_skills(command, limit=limit)
    if not matches:
        return ""
    lines = []
    for skill in matches:
        lines.append(f"{skill.get('title')}: {skill.get('text')}")
    return "\n".join(lines)
