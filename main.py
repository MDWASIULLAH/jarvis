import datetime
import ast
import asyncio
import ctypes
import difflib
import html
import importlib.util
import json
import mimetypes
import operator
import os
import random
import re
import shutil
import smtplib
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from email.message import EmailMessage
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import eel

try:
    from jarvis_agent import clean_open_target, plan_task, strip_wake_word
except Exception:
    clean_open_target = None
    plan_task = None
    strip_wake_word = None

pywhatkit = None
PYWHATKIT_UNAVAILABLE = False
BRAIN_MODULE = None
SKILLS_MODULE = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "jarvis_data"
FILES_DIR = DATA_DIR / "files"
NOTES_FILE = DATA_DIR / "notes.txt"
SETTINGS_FILE = DATA_DIR / "settings.json"
CORE_HOST = "127.0.0.1"
CORE_PORT = int(os.getenv("JARVIS_CORE_PORT", "8765"))
AUTO_SCROLL_STOP = threading.Event()
AUTO_SCROLL_THREAD = None
OLLAMA_UNAVAILABLE_UNTIL = 0.0

eel.init("www")


def _load_env_file() -> None:
    for env_file in (BASE_DIR / ".env", BASE_DIR / ".env.local"):
        if not env_file.exists():
            continue
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                text = line.strip()
                if not text or text.startswith("#") or "=" not in text:
                    continue
                key, value = text.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception:
            continue


_load_env_file()


def _brain():
    global BRAIN_MODULE

    if BRAIN_MODULE is None:
        BRAIN_MODULE = __import__("jarvis_brain")
    return BRAIN_MODULE


def _skills():
    global SKILLS_MODULE

    if SKILLS_MODULE is None:
        SKILLS_MODULE = __import__("jarvis_skills")
    return SKILLS_MODULE


def add_intent_example(*args, **kwargs):
    return _brain().add_intent_example(*args, **kwargs)


def add_knowledge(*args, **kwargs):
    return _brain().add_knowledge(*args, **kwargs)


def add_link(*args, **kwargs):
    return _brain().add_link(*args, **kwargs)


def answer_with_rag(*args, **kwargs):
    return _brain().answer_with_rag(*args, **kwargs)


def predict_intent(*args, **kwargs):
    return _brain().predict_intent(*args, **kwargs)


def train_intent_model(*args, **kwargs):
    return _brain().train_intent_model(*args, **kwargs)


def import_dataset(*args, **kwargs):
    return _brain().import_dataset(*args, **kwargs)


def install_default_skills(*args, **kwargs):
    return _skills().install_default_skills(*args, **kwargs)


def skill_status(*args, **kwargs):
    return _skills().skill_status(*args, **kwargs)


def skill_context(*args, **kwargs):
    return _skills().skill_context(*args, **kwargs)

JOKES = [
    "I would tell you a UDP joke, but you might not get it.",
    "Why did the programmer quit his job? Because he didn't get arrays.",
    "I only know 25 letters of the alphabet. I don't know y.",
]

WEBSITE_ALIASES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com",
    "whatsapp web": "https://web.whatsapp.com",
}

APP_ALIASES = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "chrome.exe",
    ],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "paint": ["mspaint.exe"],
    "task manager": ["taskmgr.exe"],
    "vscode": ["code.exe", r"C:\Users\Public\Desktop\Visual Studio Code.lnk"],
    "vs code": ["code.exe", r"C:\Users\Public\Desktop\Visual Studio Code.lnk"],
    "code": ["code.exe", r"C:\Users\Public\Desktop\Visual Studio Code.lnk"],
    "visual studio code": ["code.exe", r"C:\Users\Public\Desktop\Visual Studio Code.lnk"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "powerpoint": ["powerpnt.exe"],
    "outlook": ["outlook.exe"],
    "spotify": ["spotify.exe"],
    "whatsapp": ["whatsapp.exe"],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "windows terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
}

TERMINAL_TARGETS = {"terminal", "windows terminal", "command prompt", "cmd", "powershell", "shell"}

FOLDER_ALIASES = {
    "desktop": Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "music": Path.home() / "Music",
    "pictures": Path.home() / "Pictures",
    "videos": Path.home() / "Videos",
}

PENDING_EMAIL = {
    "to": None,
    "subject": None,
    "body": None,
}
PENDING_SHARE = {
    "target": None,
    "message": None,
    "number": None,
}
PENDING_TERMINAL = {
    "command": None,
}
PENDING_ACTION = None

DEFAULT_SETTINGS = {
    "security_level": "HIGH",
    "permission_email": True,
    "permission_share": True,
    "permission_danger": True,
    "api_enabled": False,
    "api_key": "",
    "api_endpoint": "https://api.openai.com/v1/chat/completions",
    "api_model": "gpt-4o-mini",
    "searxng_url": "",
    "daily_briefing": True,
    "whatsapp_number": "",
    "ollama_model": "qwen2.5-coder:7b",
    "google_client_id": "",
    "supabase_url": "",
    "supabase_anon_key": "",
    "work_mode": "simple",
    "voice_enabled": True,
    "aliases": {},
}

CORRECTION_MAP = {
    "opne": "open",
    "openi": "open",
    "oppen": "open",
    "claculator": "calculator",
    "calclator": "calculator",
    "calcultor": "calculator",
    "calculater": "calculator",
    "calcuator": "calculator",
    "calculaor": "calculator",
    "calcualte": "calculate",
    "calcuate": "calculate",
    "calulate": "calculate",
    "inti": "into",
    "intoo": "into",
    "notpad": "notepad",
    "noepad": "notepad",
    "gogle": "google",
    "gooogle": "google",
    "youtub": "youtube",
    "youtbe": "youtube",
    "whatsap": "whatsapp",
    "whatapp": "whatsapp",
    "whatsaap": "whatsapp",
    "crowl": "crawl",
    "crawel": "crawl",
    "scape": "scrape",
    "scrap": "scrape",
    "emal": "email",
    "mail": "email",
    "newas": "news",
    "neaws": "news",
    "bussines": "business",
    "busines": "business",
    "sprot": "sport",
    "sprots": "sports",
    "breifing": "briefing",
    "sumarize": "summarize",
    "serch": "search",
    "seach": "search",
    "writ": "write",
    "wrte": "write",
    "wrtie": "write",
    "rite": "write",
    "reed": "read",
    "red": "read",
    "shoets": "shorts",
    "shoet": "shorts",
    "shot": "shorts",
    "shots": "shorts",
    "windo": "windows",
    "linkk": "link",
    "wikipidia": "wikipedia",
    "wikipidea": "wikipedia",
}

VOCABULARY = {
    "open",
    "launch",
    "start",
    "run",
    "calculator",
    "calculate",
    "compute",
    "solve",
    "plus",
    "minus",
    "multiply",
    "times",
    "into",
    "divide",
    "notepad",
    "chrome",
    "edge",
    "google",
    "youtube",
    "github",
    "whatsapp",
    "email",
    "search",
    "write",
    "read",
    "note",
    "file",
    "news",
    "business",
    "sports",
    "ai",
    "technology",
    "world",
    "india",
    "briefing",
    "today",
    "daily",
    "share",
    "send",
    "summarize",
    "settings",
    "security",
    "api",
    "key",
    "skill",
    "skills",
    "crawl",
    "scrape",
    "scraping",
    "crawling",
    "crawl4ai",
    "scrapy",
    "playwright",
    "shorts",
    "scroll",
    "stop",
    "link",
    "wikipedia",
    "code",
    "website",
    "site",
    "page",
    "frontend",
    "python",
    "javascript",
    "html",
    "css",
}


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _normalized(text: str) -> str:
    return _squash(text).lower()


def _strip_wake_prefix(command: str) -> str:
    if strip_wake_word:
        return strip_wake_word(command)
    text = _squash(command)
    text = re.sub(r"^(hey|hi|hello|ok|okay)\s+jarvis[,\s:;-]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^jarvis[,\s:;-]+", "", text, flags=re.IGNORECASE)
    return _squash(text)


def _clean_open_target(raw_target: str) -> str:
    if clean_open_target:
        return clean_open_target(raw_target)
    target = _squash(raw_target).strip(" .,!?:;")
    target = re.sub(r"^(my|the|a|an)\s+", "", target, flags=re.IGNORECASE)
    target = re.sub(r"\s+(app|application|program|software)$", "", target, flags=re.IGNORECASE)
    if _normalized(target) in {"vs code", "vscode", "visual code"}:
        return "visual studio code"
    return target


def _strip_markdown_noise(text: str, preserve_code: bool = False) -> str:
    source = str(text or "").replace("\r\n", "\n")
    source = re.sub(r"<!--[\s\S]*?-->", " ", source)
    code_blocks: list[str] = []

    if preserve_code:
        def stash_code(match):
            code_blocks.append(match.group(0))
            return f"@@JARVIS_CODE_BLOCK_{len(code_blocks) - 1}@@"

        source = re.sub(r"```[\s\S]*?```", stash_code, source)
    else:
        source = re.sub(r"```[a-zA-Z0-9+#-]*\s*[\s\S]*?```", " ", source)

    cleaned_lines = []
    previous = ""
    for raw_line in source.split("\n"):
        line = raw_line.strip()
        lowered_line = line.lower()
        if any(
            marker in lowered_line
            for marker in [
                "markdownlint-disable",
                "shields.io",
                "badge.svg",
                "<img",
                "<picture",
                "<div",
                "</div",
                "<br",
                "align=\"center\"",
            ]
        ):
            continue
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        if re.fullmatch(r"[*_\-]{3,}", line):
            continue
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s*>\s*", "", line)
        line = re.sub(r"^\s*[-*]\s*>\s*", "- ", line)
        line = re.sub(r"\s+#{1,6}\s+", " ", line)
        line = re.sub(r"\s+>\s*", " ", line)
        line = re.sub(r"\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*", r"\1: ", line, flags=re.IGNORECASE)
        line = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", line)
        line = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 - \2", line)
        line = re.sub(r"<[^>]+>", " ", line)
        line = re.sub(r"^GitHub README:\s*", "", line, flags=re.IGNORECASE)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)
        line = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", line)
        line = re.sub(r"`{1,2}([^`\n]+)`{1,2}", r"\1", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and line != previous:
            cleaned_lines.append(line)
            previous = line

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if preserve_code:
        for index, block in enumerate(code_blocks):
            cleaned = cleaned.replace(f"@@JARVIS_CODE_BLOCK_{index}@@", block.strip())

    return cleaned


def _shorten_long_answer(text: str, max_words: int = 170) -> str:
    cleaned = _strip_markdown_noise(text, preserve_code=False)
    words = cleaned.split()
    if len(words) <= max_words:
        return cleaned

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    selected = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        selected.append(sentence.strip())
        if len(" ".join(selected).split()) >= max_words:
            break
    if not selected:
        selected = [" ".join(words[:max_words])]
    return " ".join(selected).strip() + "..."


def _is_noise_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    return any(
        marker in lowered
        for marker in [
            "github readme",
            "markdownlint",
            "shields.io",
            "badge.svg",
            "raw=true",
            "discord.gg",
            "deepseek.com/",
            "huggingface.co/",
            "license",
            "homepage",
            "chat deepseek",
            "download",
            "logo.svg",
            "clone our",
            "git clone",
            "convert.py",
            "--hf-ckpt-path",
            "--save-path",
        ]
    ) or lowered.count("http") >= 2 or len(sentence.split()) > 45


def _best_lead_sentence(query: str, text: str) -> str:
    sentences = [
        _squash(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+", _strip_markdown_noise(text, preserve_code=False))
        if len(_squash(sentence).split()) >= 5 and not _is_noise_sentence(sentence)
    ]
    if not sentences:
        return ""

    keywords = {
        word
        for word in re.findall(r"[a-zA-Z0-9]+", query.lower())
        if len(word) > 2 and word not in {"what", "who", "where", "when", "why", "how", "tell", "about", "latest", "news"}
    }
    priority_terms = ("not supported", "supports", "requires", "only", "is ", "are ", "current", "latest")
    scored = []
    for index, sentence in enumerate(sentences[:12]):
        lowered = sentence.lower()
        keyword_score = sum(2 for word in keywords if word in lowered)
        priority_score = sum(1 for term in priority_terms if term in lowered)
        scored.append((keyword_score + priority_score, -index, sentence))
    scored.sort(reverse=True)
    return scored[0][2] if scored else sentences[0]


def _polish_answer_from_context(query: str, text: str, max_words: int = 150) -> str:
    cleaned = _shorten_long_answer(text, max_words=max_words)
    lead = _best_lead_sentence(query, cleaned)
    if lead:
        keywords = {
            word
            for word in re.findall(r"[a-zA-Z0-9]+", query.lower())
            if len(word) > 2 and word not in {"what", "who", "where", "when", "why", "how", "tell", "about", "latest", "news"}
        }
        important_terms = ("require", "requires", "dependency", "dependencies", "linux", "windows", "mac", "not supported", "supported", "python", "torch", "triton")
        details = []
        for sentence in re.split(r"(?<=[.!?])\s+", cleaned):
            sentence = _squash(sentence)
            if not sentence or sentence == lead or _is_noise_sentence(sentence):
                continue
            lowered = sentence.lower()
            if re.search(r"\b(git clone|cd |python\s+\S+\.py|pip install|conda|uv\s+|navigate to|first, clone|run then)\b", lowered):
                continue
            if any(word in lowered for word in keywords) or any(term in lowered for term in important_terms):
                if sentence not in details:
                    details.append(sentence)
            if len(" ".join(details).split()) >= 85 or len(details) >= 4:
                break
        if details:
            return f"{lead}\n\nDetails:\n\n" + "\n".join(f"- {item}" for item in details)
        return lead
    return cleaned


def _is_identity_question(command: str) -> bool:
    normalized = _normalized(command).replace("what's", "whats")
    return bool(
        re.fullmatch(r"(whats|what is|tell me)\s+(your|you)\s+name\??", normalized)
        or re.fullmatch(r"(who are you|what are you|introduce yourself)\??", normalized)
        or re.fullmatch(r"(your name|name)\??", normalized)
    )


def _jarvis_identity_answer() -> str:
    return (
        "My name is Jarvis.\n\n"
        "I am your local desktop AI assistant. I can answer questions, search with the free local stack, "
        "write code, read links, open apps, and draft messages or emails after asking permission."
    )


def _json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _response(message: str, kind: str = "response", speak_result: bool = False, **extra) -> str:
    if kind not in {"code", "terminal"}:
        message = _strip_markdown_noise(message)
    payload = {"type": kind, "message": message}
    payload.update(extra)
    if speak_result:
        speak(message)
    return _json(payload)


def _google_client_id() -> str:
    settings = _load_settings()
    return _squash(os.getenv("GOOGLE_CLIENT_ID", "") or settings.get("google_client_id", ""))


def _first_env(*names: str) -> str:
    for name in names:
        value = _squash(os.getenv(name, ""))
        if value:
            return value
    return ""


def _supabase_config() -> dict:
    settings = _load_settings()
    supabase_url = _first_env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "VITE_SUPABASE_URL") or _squash(settings.get("supabase_url", ""))
    supabase_key = (
        _first_env(
            "SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
            "SUPABASE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
            "VITE_SUPABASE_ANON_KEY",
            "VITE_SUPABASE_PUBLISHABLE_KEY",
        )
        or _squash(settings.get("supabase_anon_key", ""))
    )
    return {"url": supabase_url, "anon_key": supabase_key}


def _route_command(command: str) -> dict:
    normalized = _normalized(command)
    route = {
        "input": command,
        "intent": "chat",
        "search_needed": False,
        "retrieval_needed": False,
        "steps": ["User Input", "Router"],
    }

    if re.search(r"\b(today|latest|current|news|briefing)\b", normalized):
        route.update({"intent": "news", "search_needed": True})
        route["steps"] += ["Web Search / Retrieval", "Context + Docs", "LLM", "Final Answer"]
    elif re.search(r"\b(tell me about|what is|who is|where is|explain|describe|define|information about|details about)\b", normalized):
        route.update({"intent": "answer", "search_needed": True, "retrieval_needed": True})
        route["steps"] += ["RAG Memory", "Web Search / Retrieval", "Context + Docs", "LLM", "Final Answer"]
    elif re.search(r"https?://|www\.", normalized):
        route.update({"intent": "read_link", "retrieval_needed": True})
        route["steps"] += ["Web Search / Retrieval", "Context + Docs", "LLM", "Final Answer"]
    elif re.search(r"\b(code|program|website|react|next|python|javascript|html|css)\b", normalized):
        route.update({"intent": "code", "retrieval_needed": True})
        route["steps"] += ["RAG Memory", "Context + Docs", "LLM", "Final Answer"]
    elif re.search(r"\b(train|dataset|kaggle|knowledge|rag|learn|skill|skills)\b", normalized):
        route.update({"intent": "training", "retrieval_needed": True})
        route["steps"] += ["Dataset / RAG Store", "Final Answer"]
    elif _is_open_command(command):
        route.update({"intent": "app_control"})
        route["steps"] += ["Permission / Safe Action", "Final Answer"]
    else:
        route["steps"] += ["Local Reasoning", "Final Answer"]

    return route


def _ensure_data_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)


def _load_settings() -> dict:
    _ensure_data_dirs()
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        settings = DEFAULT_SETTINGS.copy()
        if isinstance(saved, dict):
            for key, value in saved.items():
                if key in DEFAULT_SETTINGS:
                    settings[key] = value
        return settings
    except Exception:
        return DEFAULT_SETTINGS.copy()


def _save_settings(updates: dict) -> dict:
    settings = _load_settings()
    for key, value in updates.items():
        if key in DEFAULT_SETTINGS:
            settings[key] = value
    settings["security_level"] = "HIGH"
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings


def _public_settings(settings: dict | None = None) -> dict:
    data = (settings or _load_settings()).copy()
    data["api_key_saved"] = bool(data.get("api_key"))
    data["api_key"] = ""
    return data


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _search_stack_status(settings: dict | None = None) -> dict:
    current = settings or _load_settings()
    return {
        "provider": "free-open-source",
        "ddgs": _module_available("duckduckgo_search") or _module_available("ddgs"),
        "searxng": bool(_squash(current.get("searxng_url", "")) or os.getenv("SEARXNG_URL", "")),
        "crawl4ai": _module_available("crawl4ai"),
        "playwright": _module_available("playwright"),
        "beautifulsoup": _module_available("bs4"),
        "requests": _module_available("requests"),
    }


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._ -]", "", name or "").strip().strip(".")
    if not cleaned:
        return "jarvis-note.txt"
    return cleaned[:80]


def _correct_word(word: str) -> tuple[str, bool]:
    prefix = re.match(r"^\W*", word).group(0)
    suffix = re.search(r"\W*$", word).group(0)
    core = word[len(prefix): len(word) - len(suffix) if suffix else len(word)]
    lowered = core.lower()

    if not core:
        return word, False

    replacement = CORRECTION_MAP.get(lowered)
    if replacement is None and len(lowered) >= 4:
        matches = difflib.get_close_matches(lowered, VOCABULARY, n=1, cutoff=0.82)
        replacement = matches[0] if matches else None

    if not replacement or replacement == lowered:
        return word, False

    if core[:1].isupper():
        replacement = replacement.capitalize()
    return f"{prefix}{replacement}{suffix}", True


def _correct_command(command: str) -> tuple[str, list[str]]:
    text = _squash(command)
    settings = _load_settings()
    aliases = settings.get("aliases", {}) if isinstance(settings.get("aliases"), dict) else {}

    lowered = text.lower()
    if lowered in aliases:
        return aliases[lowered], [f"{text} -> {aliases[lowered]}"]

    corrected_words = []
    fixes = []
    for word in text.split(" "):
        corrected, changed = _correct_word(word)
        corrected_words.append(corrected)
        if changed:
            fixes.append(f"{word} -> {corrected}")

    corrected_text = " ".join(corrected_words)
    phrase_fixes = [
        (r"\bopen\s+calc\b", "open calculator"),
        (r"\bsend\s+whatsapp\b", "share to whatsapp"),
        (r"\bdaily\s+news\b", "daily briefing"),
        (r"\btoday\s+news\b", "daily briefing"),
        (r"\bshow\s+news\b", "daily briefing"),
    ]
    for pattern, replacement in phrase_fixes:
        new_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
        if new_text != corrected_text:
            fixes.append(f"{corrected_text} -> {new_text}")
            corrected_text = new_text

    return corrected_text, fixes


def _learn_alias(command: str) -> str | None:
    normalized = _normalized(command)
    if normalized.startswith(("learn intent ", "train intent ", "learn knowledge ", "learn link ", "learn url ", "learn this ")):
        return None

    match = re.search(r"learn\s+(.+?)\s+(?:means|as)\s+(.+)$", command, re.IGNORECASE)
    if not match:
        return None

    phrase = _normalized(match.group(1))
    meaning = _squash(match.group(2))
    if not phrase or not meaning:
        return "Use: learn clac means open calculator."

    settings = _load_settings()
    aliases = settings.get("aliases", {}) if isinstance(settings.get("aliases"), dict) else {}
    aliases[phrase] = meaning
    _save_settings({"aliases": aliases})
    return f"Learned: {phrase} means {meaning}."


def _speak_setup():
    if pyttsx3 is None:
        return None

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 178)
        return engine
    except Exception:
        return None


TTS_ENGINE = None
TTS_LOCK = threading.Lock()


def speak(text: str) -> None:
    if not text or pyttsx3 is None:
        return

    def run() -> None:
        global TTS_ENGINE
        try:
            with TTS_LOCK:
                if TTS_ENGINE is None:
                    TTS_ENGINE = _speak_setup()
                if TTS_ENGINE is None:
                    return
                TTS_ENGINE.say(text)
                TTS_ENGINE.runAndWait()
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()


def _open_url(url: str, message: str) -> str:
    webbrowser.open(url)
    return message


def _launch_known_app(candidates: list[str]) -> bool:
    for candidate in candidates:
        try:
            candidate_path = Path(candidate)
            if candidate_path.is_absolute() and candidate_path.exists():
                subprocess.Popen([str(candidate_path)])
                return True
            resolved = shutil.which(candidate)
            if resolved:
                subprocess.Popen([resolved])
                return True
        except Exception:
            continue
    return False


def _open_real_terminal() -> str:
    if os.name != "nt":
        return "Real terminal launch is only available on Windows in this desktop build."

    base_dir = str(BASE_DIR)
    ps_dir = base_dir.replace("'", "''")
    windows_terminal = Path.home() / "AppData/Local/Microsoft/WindowsApps/wt.exe"
    commands = []
    if windows_terminal.exists():
        commands.append([str(windows_terminal), "-d", base_dir])
    commands.extend([
        ["wt.exe", "-d", base_dir],
        ["powershell.exe", "-NoExit", "-Command", f"Set-Location -LiteralPath '{ps_dir}'"],
        ["cmd.exe", "/K", f'cd /d "{base_dir}"'],
    ])

    creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    for command in commands:
        executable = command[0]
        path = Path(executable)
        if path.is_absolute():
            if not path.exists():
                continue
            resolved = executable
        else:
            resolved = shutil.which(executable)
            if not resolved:
                continue
        try:
            subprocess.Popen([resolved, *command[1:]], cwd=base_dir, creationflags=creation_flags)
            return "Opening real Windows terminal in the Jarvis folder. Running commands still requires approval inside Jarvis."
        except Exception:
            continue

    return "I could not open Windows Terminal, PowerShell, or Command Prompt on this computer."


def _shortcut_roots() -> list[Path]:
    appdata = os.getenv("APPDATA")
    programdata = os.getenv("PROGRAMDATA")
    roots = [
        Path.home() / "Desktop",
        Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs",
    ]
    if appdata:
        roots.append(Path(appdata) / "Microsoft/Windows/Start Menu/Programs")
    if programdata:
        roots.append(Path(programdata) / "Microsoft/Windows/Start Menu/Programs")
    return roots


def _launch_shortcut(target: str) -> bool:
    normalized_target = _normalized(target)
    shortcuts = []
    for root in _shortcut_roots():
        if not root.exists():
            continue
        try:
            for shortcut in root.rglob("*.lnk"):
                shortcuts.append(shortcut)
        except Exception:
            continue

    exact = [item for item in shortcuts if _normalized(item.stem) == normalized_target]
    candidates = exact or [
        item for item in shortcuts
        if normalized_target in _normalized(item.stem) or _normalized(item.stem) in normalized_target
    ]

    if not candidates:
        names = {_normalized(item.stem): item for item in shortcuts}
        close = difflib.get_close_matches(normalized_target, names.keys(), n=1, cutoff=0.78)
        candidates = [names[close[0]]] if close else []

    if not candidates:
        return False

    try:
        os.startfile(candidates[0])  # type: ignore[attr-defined]
        return True
    except Exception:
        return False


def _open_folder(path: Path, label: str) -> str:
    if not path.exists():
        return f"I could not find {label}."

    try:
        os.startfile(path)  # type: ignore[attr-defined]
        return f"Opening {label}."
    except Exception:
        return f"I could not open {label}."


def _open_target(raw_target: str) -> str:
    target = _normalized(raw_target)
    display_target = _squash(raw_target)

    if not target:
        return "Tell me what app or website to open."

    if target in TERMINAL_TARGETS:
        return _open_real_terminal()

    if target in FOLDER_ALIASES:
        return _open_folder(FOLDER_ALIASES[target], display_target.title())

    if target in WEBSITE_ALIASES:
        return _open_url(WEBSITE_ALIASES[target], f"Opening {display_target}.")

    if target.startswith("youtube"):
        if "short" in target:
            return _open_url("https://www.youtube.com/shorts", "Opening YouTube Shorts.")
        query = _extract_after(display_target, ["youtube"])
        if query:
            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
            return _open_url(url, f"Searching YouTube for {query}.")
        return _open_url("https://www.youtube.com", "Opening YouTube.")

    if target.startswith("wikipedia"):
        topic = _extract_after(display_target, ["wikipedia", "of", "about"])
        topic = re.sub(r"\b(and\s+)?(read|open|show|for me|to me|it)\b", " ", topic, flags=re.IGNORECASE)
        topic = _squash(topic)
        if topic:
            webbrowser.open("https://en.wikipedia.org/wiki/" + urllib.parse.quote(topic.replace(" ", "_")))
            summary = _wikipedia_summary(topic)
            return summary or f"Opening Wikipedia for {topic}."
        return _open_url("https://www.wikipedia.org", "Opening Wikipedia.")

    if re.match(r"^https?://", display_target, flags=re.IGNORECASE):
        return _open_url(display_target, f"Opening {display_target}.")

    if "." in target and " " not in target:
        return _open_url(f"https://{target}", f"Opening {display_target}.")

    candidates = APP_ALIASES.get(target, [f"{target}.exe", target])
    if _launch_known_app(candidates):
        return f"Opening {display_target}."

    app_match = difflib.get_close_matches(target, APP_ALIASES.keys(), n=1, cutoff=0.78)
    if app_match and _launch_known_app(APP_ALIASES[app_match[0]]):
        return f"Opening {app_match[0]}."

    if _launch_shortcut(display_target):
        return f"Opening {display_target}."

    return f"I could not safely find {display_target}. I did not ask Windows to run the raw text."


def _confirm_open_target(raw_target: str, original_command: str = "") -> str:
    global PENDING_ACTION
    target = _clean_open_target(raw_target)
    plan = plan_task(original_command or f"open {target}") if plan_task else {
        "intent": "open_app_or_site",
        "risk": "medium",
        "target": target,
        "steps": ["Ask for approval", f"Open {target} through Local Core"],
    }
    PENDING_ACTION = {"type": "open_target", "target": target, "plan": plan}
    return _response(
        f"Approve opening {target}?",
        "confirm_action",
        action="open_target",
        plan=plan,
        target=target,
    )


MATH_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_math(expression: str) -> float | int:
    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in MATH_OPERATORS:
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Power is too large.")
            return MATH_OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in MATH_OPERATORS:
            return MATH_OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("Only basic math is allowed.")

    parsed = ast.parse(expression, mode="eval")
    return evaluate(parsed)


def _format_number(value: float | int) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _spoken_math_to_expression(text: str) -> str:
    expression = _normalized(text)
    replacements = [
        (r"\bmultiplied\s+by\b", "*"),
        (r"\bmultiply\s+by\b", "*"),
        (r"\bmultiply\b", "*"),
        (r"\btimes\b", "*"),
        (r"\binto\b", "*"),
        (r"\bx\b", "*"),
        (r"\bplus\b", "+"),
        (r"\badd\b", "+"),
        (r"\bminus\b", "-"),
        (r"\bsubtract\b", "-"),
        (r"\bdivided\s+by\b", "/"),
        (r"\bdivide\s+by\b", "/"),
        (r"\bdivide\b", "/"),
        (r"\bover\b", "/"),
    ]
    for pattern, replacement in replacements:
        expression = re.sub(pattern, f" {replacement} ", expression, flags=re.IGNORECASE)
    expression = expression.replace("×", "*").replace("÷", "/")
    expression = re.sub(r"[^0-9+\-*/().% ]", " ", expression)
    expression = _squash(expression)
    return expression


def _extract_calculation(command: str) -> tuple[str, str] | None:
    normalized = _normalized(command)
    if not re.search(r"\d", normalized):
        return None
    if not any(word in normalized for word in ["calculate", "compute", "solve", "what is", "how much", "plus", "minus", "multiply", "times", "into", "divided", "divide", " x "]):
        return None

    tail = command
    keyword_match = re.search(r"\b(?:calculate|compute|solve|what\s+is|how\s+much\s+is)\b(.+)$", command, re.IGNORECASE)
    if keyword_match:
        tail = keyword_match.group(1)
    elif "calculator" in normalized:
        tail = re.sub(r"^.*?\bcalculator\b", "", command, flags=re.IGNORECASE)

    tail = re.sub(r"\b(?:and\s+then|then|please|for\s+me|answer|answe|open|calculator)\b", " ", tail, flags=re.IGNORECASE)
    expression = _spoken_math_to_expression(tail)
    if not re.search(r"\d", expression) or not re.search(r"[+\-*/%]", expression):
        return None

    try:
        result = _safe_eval_math(expression)
    except Exception:
        return None

    display_expression = expression.replace("*", "×").replace("/", "÷")
    return display_expression, _format_number(result)


def _handle_calculation_command(command: str) -> str | None:
    calculation = _extract_calculation(command)
    if not calculation:
        return None

    expression, result = calculation
    opened = ""
    if "calculator" in _normalized(command) or re.match(r"^(open|launch|start)\b", command, re.IGNORECASE):
        opened = _open_target("calculator") + " "
    return f"{opened}{expression} = {result}."


def _search_web(query: str) -> str:
    query = _squash(query)
    if not query:
        return "Tell me what to search for."
    data = _open_source_search(query)
    if data:
        return _format_open_source_search_answer(query, data)
    fallback_url = "https://duckduckgo.com/?q=" + urllib.parse.quote_plus(query)
    return (
        "Local open-source search did not return results. "
        "Check the internet connection or add a self-hosted SearXNG URL in Settings. "
        f"Browser fallback URL: {fallback_url}"
    )


def _search_topic_for_query(query: str) -> str:
    normalized = _normalized(query)
    if re.search(r"\b(news|briefing|latest|today|current|sports|business|market|finance|stock|ai|technology|world|india)\b", normalized):
        if re.search(r"\b(finance|financial|market|markets|stock|stocks|economy|business)\b", normalized):
            return "finance"
        return "news"
    return "general"


def _source_name_from_url(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
        return host.removeprefix("www.")
    except Exception:
        return ""


def _clean_duckduckgo_url(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return query["uddg"][0]
    return url


def _normalize_search_results(raw_results: list[dict], provider: str) -> list[dict]:
    results = []
    seen = set()
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        title = _squash(str(item.get("title") or item.get("name") or ""))
        url = _clean_duckduckgo_url(_squash(str(item.get("url") or item.get("href") or item.get("link") or "")))
        content = _squash(str(item.get("content") or item.get("body") or item.get("snippet") or item.get("summary") or ""))
        published = _squash(str(item.get("published") or item.get("published_date") or item.get("date") or ""))
        source = _squash(str(item.get("source") or _source_name_from_url(url)))
        if not title and not content:
            continue
        key = (title.lower(), url.lower())
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "title": title or source or "Search result",
                "url": url,
                "content": content,
                "published": published,
                "source": source,
                "provider": provider,
            }
        )
    return results


def _searxng_search(query: str, max_results: int = 5) -> list[dict]:
    settings = _load_settings()
    base = _squash(settings.get("searxng_url", "") or os.getenv("SEARXNG_URL", ""))
    if not base:
        return []
    try:
        params = urllib.parse.urlencode(
            {
                "q": query,
                "format": "json",
                "language": "en",
                "safesearch": "1",
            }
        )
        url = base.rstrip("/") + "/search?" + params
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "JarvisLocalCore/1.0"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read(1_500_000).decode("utf-8", errors="ignore"))
        return _normalize_search_results(data.get("results", [])[:max_results], "SearXNG")
    except Exception:
        return []


def _ddgs_search(query: str, topic: str | None = None, max_results: int = 5) -> list[dict]:
    try:
        try:
            from ddgs import DDGS
        except Exception:
            from duckduckgo_search import DDGS
    except Exception:
        return []

    max_results = max(1, min(int(max_results), 10))
    wants_news = topic == "news" or _search_topic_for_query(query) == "news"
    try:
        with DDGS() as ddgs:
            if wants_news and hasattr(ddgs, "news"):
                raw = list(ddgs.news(query, region="in-en", safesearch="moderate", timelimit="d", max_results=max_results))
            else:
                raw = list(ddgs.text(query, region="in-en", safesearch="moderate", timelimit="d" if wants_news else None, max_results=max_results))
        return _normalize_search_results(raw, "DDGS")
    except TypeError:
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
            return _normalize_search_results(raw, "DDGS")
        except Exception:
            return []
    except Exception:
        return []


def _duckduckgo_html_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return []

    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    try:
        try:
            import requests

            response = requests.get(
                url,
                headers={"User-Agent": "JarvisLocalCore/1.0"},
                timeout=12,
            )
            response.raise_for_status()
            html_text = response.text
        except Exception:
            request = urllib.request.Request(url, headers={"User-Agent": "JarvisLocalCore/1.0"})
            with urllib.request.urlopen(request, timeout=12) as response:
                html_text = response.read(1_500_000).decode("utf-8", errors="ignore")
    except Exception:
        return []

    soup = BeautifulSoup(html_text, "html.parser")
    raw = []
    for result in soup.select(".result")[: max(1, min(int(max_results), 10))]:
        title_link = result.select_one(".result__title a") or result.select_one("a.result__a")
        snippet = result.select_one(".result__snippet") or result.select_one(".result__body")
        if not title_link:
            continue
        raw.append(
            {
                "title": title_link.get_text(" ", strip=True),
                "url": title_link.get("href", ""),
                "content": snippet.get_text(" ", strip=True) if snippet else "",
            }
        )
    return _normalize_search_results(raw, "DuckDuckGo HTML")


def _result_sentences(text: str) -> list[str]:
    text = _squash(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [_squash(part) for part in parts if len(_squash(part)) > 25]


def _summarize_search_results(query: str, results: list[dict]) -> str:
    snippets = []
    for item in results[:5]:
        snippet = _squash(item.get("content", ""))
        if snippet:
            snippets.extend(_result_sentences(snippet))

    if not snippets:
        names = ", ".join(item.get("title", "source") for item in results[:3])
        return f"I found results for {query}. Strong starting sources: {names}."

    keywords = {
        word
        for word in re.findall(r"[a-zA-Z0-9]+", query.lower())
        if len(word) > 2 and word not in {"the", "and", "for", "with", "about", "latest", "news"}
    }
    scored = []
    for index, sentence in enumerate(snippets):
        lowered = sentence.lower()
        score = sum(1 for word in keywords if word in lowered)
        scored.append((score, -index, sentence))
    scored.sort(reverse=True)

    selected = []
    for _score, _order, sentence in scored:
        if sentence not in selected:
            selected.append(sentence)
        if len(" ".join(selected).split()) >= 90 or len(selected) >= 4:
            break
    return " ".join(selected)[:900]


def _open_source_search(query: str, topic: str | None = None, max_results: int = 5) -> dict | None:
    topic = topic or _search_topic_for_query(query)
    results = _searxng_search(query, max_results=max_results)
    provider = "SearXNG" if results else ""
    if not results:
        results = _ddgs_search(query, topic=topic, max_results=max_results)
        provider = "DDGS" if results else ""
    if not results:
        results = _duckduckgo_html_search(query, max_results=max_results)
        provider = "DuckDuckGo HTML" if results else ""
    if not results:
        return None
    return {
        "provider": provider,
        "topic": topic,
        "answer": _summarize_search_results(query, results),
        "results": results[:max_results],
    }


def _format_open_source_search_answer(query: str, data: dict) -> str:
    lines = []
    answer = _squash(data.get("answer", ""))
    if answer:
        lines.append(_polish_answer_from_context(query, answer, max_words=125))
    else:
        lines.append(f"I found these sources for {query}.")

    results = data.get("results", []) if isinstance(data.get("results"), list) else []
    if results:
        lines.append("")
        lines.append("Sources:")
        for index, item in enumerate(results[:5], 1):
            title = _squash(item.get("title", "")) or "Source"
            url = _squash(item.get("url", ""))
            content = _squash(item.get("content", ""))
            source_line = f"{index}. {title}"
            if url:
                source_line += f" - {url}"
            if content:
                snippet = _strip_markdown_noise(content)
                source_line += f"\n   {snippet[:220]}"
            lines.append(source_line)

    if len(lines) <= 1:
        return f"I searched the free local stack for {query}, but it did not return a readable answer."
    return "\n".join(lines)


def _extract_after(command: str, anchors: list[str]) -> str:
    text = command
    for anchor in anchors:
        text = re.sub(rf"\b{re.escape(anchor)}\b", " ", text, flags=re.IGNORECASE)
    return _squash(text).strip(" ,.;:")


def _parse_email_request(command: str) -> dict:
    recipient_match = re.search(
        r"(?:send|compose|write|draft)\s+(?:an\s+)?email\s+(?:to|for)\s+(.+?)(?:\s+(?:subject|body|message|saying|say|about|regarding|for)\b|$)",
        command,
        re.IGNORECASE,
    )
    subject_match = re.search(
        r"subject\s+(.+?)(?:\s+(?:body|message|saying|say|about|regarding|for)\b|$)",
        command,
        re.IGNORECASE,
    )
    body_match = re.search(
        r"(?:body|message|say|saying)\s+(.+)$",
        command,
        re.IGNORECASE,
    )
    about_match = re.search(
        r"(?:about|regarding|for)\s+(.+)$",
        command,
        re.IGNORECASE,
    )

    body = body_match.group(1).strip() if body_match else ""
    topic = body or (about_match.group(1).strip() if about_match else "") or (subject_match.group(1).strip() if subject_match else "")
    if not body and about_match:
        body = _draft_email_body(topic)
    if not body and subject_match:
        body = _draft_email_body(topic)

    return {
        "to": recipient_match.group(1).strip().strip(",.;") if recipient_match else "",
        "subject": subject_match.group(1).strip() if subject_match else _email_subject_for_topic(topic or command),
        "body": body,
    }


def _confirm_email(payload: dict) -> str:
    global PENDING_EMAIL
    PENDING_EMAIL = payload
    message = f"Ready to send email to {payload['to']} with subject {payload['subject']}."
    return _response(message, "confirm_email", email=payload)


def _send_email() -> str:
    host = os.getenv("JARVIS_SMTP_HOST")
    port = int(os.getenv("JARVIS_SMTP_PORT", "587"))
    user = os.getenv("JARVIS_EMAIL_USER")
    password = os.getenv("JARVIS_EMAIL_PASSWORD")

    if not PENDING_EMAIL["to"]:
        return "There is no pending email to send."

    if not all([host, user, password]):
        mailto_url = (
            f"mailto:{urllib.parse.quote(PENDING_EMAIL['to'])}"
            f"?subject={urllib.parse.quote(PENDING_EMAIL['subject'] or '')}"
            f"&body={urllib.parse.quote(PENDING_EMAIL['body'] or '')}"
        )
        webbrowser.open(mailto_url)
        PENDING_EMAIL.update({"to": None, "subject": None, "body": None})
        return "Email draft opened for final review."

    message = EmailMessage()
    message["From"] = user
    message["To"] = PENDING_EMAIL["to"]
    message["Subject"] = PENDING_EMAIL["subject"]
    message.set_content(PENDING_EMAIL["body"] or "")

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(message)

    PENDING_EMAIL.update({"to": None, "subject": None, "body": None})
    return "Email sent successfully."


def _confirm_share(target: str, message: str, number: str = "") -> str:
    PENDING_SHARE.update({"target": target, "message": message, "number": number})
    return _response(
        f"Ready to share to {target}.",
        "confirm_share",
        share={"target": target, "message": message, "number": number},
    )


def _send_share() -> str:
    target = _normalized(PENDING_SHARE.get("target") or "")
    message = _squash(PENDING_SHARE.get("message") or "")
    number = re.sub(r"\D", "", PENDING_SHARE.get("number") or "")
    PENDING_SHARE.update({"target": None, "message": None, "number": None})

    if not target or not message:
        return "There is no pending share."

    encoded = urllib.parse.quote(message)
    if "whatsapp" in target:
        settings_number = re.sub(r"\D", "", _load_settings().get("whatsapp_number") or "")
        number = number or settings_number
        url = f"https://wa.me/{number}?text={encoded}" if number else f"https://wa.me/?text={encoded}"
        webbrowser.open(url)
        return "WhatsApp share draft opened for final review."

    if "email" in target or "gmail" in target:
        webbrowser.open(f"mailto:?subject=Jarvis briefing&body={encoded}")
        return "Email share draft opened for final review."

    if target in WEBSITE_ALIASES:
        webbrowser.open(WEBSITE_ALIASES[target])
        return f"Opening {target}. Message is ready in Jarvis."

    if target in APP_ALIASES:
        _open_target(target)
        return f"Opening {target}. Message is ready in Jarvis."

    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(target)}")
    return f"Opening search for {target}. Message is ready in Jarvis."


def _send_virtual_key(vk_code: int) -> None:
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.04)
        user32.keybd_event(vk_code, 0, 2, 0)
    except Exception:
        pass


def _send_mouse_scroll(clicks: int) -> None:
    try:
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, clicks * 120, 0)
    except Exception:
        pass


def _scroll_once(direction: str = "down", amount: int = 5) -> str:
    clicks = amount if direction == "up" else -amount
    _send_mouse_scroll(clicks)
    if direction == "down":
        _send_virtual_key(0x28)
    else:
        _send_virtual_key(0x26)
    return f"Scrolled {direction}."


def _auto_scroll_loop(interval: float, key_code: int, startup_delay: float = 0.0) -> None:
    if startup_delay and AUTO_SCROLL_STOP.wait(startup_delay):
        return
    while not AUTO_SCROLL_STOP.is_set():
        _send_mouse_scroll(-5)
        _send_virtual_key(key_code)
        if AUTO_SCROLL_STOP.wait(interval):
            return


def _start_auto_scroll(interval: float = 8.0, key_code: int = 0x28, startup_delay: float = 4.0) -> str:
    global AUTO_SCROLL_THREAD
    AUTO_SCROLL_STOP.set()
    if AUTO_SCROLL_THREAD and AUTO_SCROLL_THREAD.is_alive():
        AUTO_SCROLL_THREAD.join(timeout=0.4)

    AUTO_SCROLL_STOP.clear()
    AUTO_SCROLL_THREAD = threading.Thread(target=_auto_scroll_loop, args=(interval, key_code, startup_delay), daemon=True)
    AUTO_SCROLL_THREAD.start()
    return f"Auto scroll will start in {int(startup_delay)} seconds. Focus YouTube Shorts or the target app now. Say stop scrolling to stop."


def _stop_auto_scroll() -> str:
    AUTO_SCROLL_STOP.set()
    return "Auto scroll stopped."


def _confirm_auto_scroll(command: str) -> str:
    global PENDING_ACTION
    interval_match = re.search(r"every\s+(\d+)", command, re.IGNORECASE)
    interval = float(interval_match.group(1)) if interval_match else 8.0
    interval = min(max(interval, 2.0), 60.0)
    PENDING_ACTION = {"type": "auto_scroll", "interval": interval, "key_code": 0x28, "startup_delay": 4.0}
    return _response(
        f"This will scroll the focused window every {int(interval)} seconds until you say stop scrolling. After approving, focus YouTube Shorts or the target app within 4 seconds.",
        "confirm_action",
        action="auto_scroll",
    )


def _confirm_terminal(command: str) -> str:
    PENDING_TERMINAL["command"] = command
    return _response(
        f"Run terminal command: {command}",
        "confirm_terminal",
        terminal={"command": command},
    )


def _run_terminal() -> str:
    command = _squash(PENDING_TERMINAL.get("command") or "")
    PENDING_TERMINAL["command"] = None
    if not command:
        return "There is no pending terminal command."

    try:
        completed = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        output = output.strip() or f"Command exited with code {completed.returncode}."
        if len(output) > 4000:
            output = output[:4000] + "\n...output trimmed..."
        return output
    except subprocess.TimeoutExpired:
        return "Terminal command timed out after 30 seconds."
    except Exception as error:
        return f"Terminal command failed: {error}"


def _parse_share_request(command: str) -> dict | None:
    number_match = re.search(r"(?:number|phone|to)\s+(\+?\d[\d\s-]{7,})", command, re.IGNORECASE)
    number = number_match.group(1).strip() if number_match else ""

    match = re.search(
        r"(?:send|share)\s+(?:to|on)\s+(.+?)\s+(?:message|text|body)\s+(.+)$",
        command,
        re.IGNORECASE,
    )
    if match:
        return {"target": match.group(1).strip(), "message": match.group(2).strip(), "number": number}

    match = re.search(
        r"(?:send|share)\s+(.+?)\s+(?:to|on)\s+(.+)$",
        command,
        re.IGNORECASE,
    )
    if match:
        target = match.group(2).strip()
        message = match.group(1).strip()
        target = re.sub(r"\s+(?:number|phone|to)\s+\+?\d[\d\s-]{7,}.*$", "", target, flags=re.IGNORECASE).strip()
        return {"message": message, "target": target, "number": number}

    return None


class _ReadableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.text_parts = []
        self._capture_title = False
        self._capture_text = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._capture_title = True
        if tag in {"p", "li", "h1", "h2", "h3"}:
            self._capture_text = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._capture_title = False
        if tag in {"p", "li", "h1", "h2", "h3"}:
            self._capture_text = False

    def handle_data(self, data):
        text = _squash(data)
        if not text:
            return
        if self._capture_title:
            self.title_parts.append(text)
        if self._capture_text:
            self.text_parts.append(text)


def _read_link(url: str) -> str:
    url = _squash(url)
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = "https://" + url

    result = _free_scrape_url(url)
    if not result:
        return "I could not read that link. Check the URL or internet connection."
    title, body, engine = result
    return _summarize_scraped_text(title, body, url, engine)


def _summarize_scraped_text(title: str, body: str, source: str, engine: str = "local") -> str:
    title = _squash(title) or source
    cleaned_body = _strip_markdown_noise(body)
    words = _squash(cleaned_body).split()
    summary = " ".join(words[:180])
    if len(words) > 180:
        summary += "..."
    if not summary:
        summary = "I could not find readable article text on that page."
    return (
        f"{title}\n\n"
        f"{summary}\n\n"
        f"Source: {source}"
    )


def _extract_text_from_html(raw: str, source: str) -> tuple[str, str]:
    parser = _ReadableHTMLParser()
    parser.feed(raw)
    title = _squash(" ".join(parser.title_parts)) or source
    body = " ".join(parser.text_parts)
    return title, body


def _scrape_with_beautifulsoup(raw: str, url: str) -> tuple[str, str] | None:
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return None

    try:
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "canvas"]):
            tag.decompose()
        title = _squash(soup.title.get_text(" ", strip=True) if soup.title else "") or url
        article = soup.find("article") or soup.body or soup
        parts = []
        for node in article.find_all(["h1", "h2", "h3", "p", "li"], limit=220):
            text = _squash(node.get_text(" ", strip=True))
            if len(text) >= 20:
                parts.append(text)
        body = _squash(" ".join(parts))
        if body:
            return title, body
    except Exception:
        return None
    return None


def _scrape_with_crawl4ai(url: str) -> tuple[str, str] | None:
    try:
        from crawl4ai import AsyncWebCrawler
    except Exception:
        return None

    async def run():
        async with AsyncWebCrawler() as crawler:
            return await crawler.arun(url=url)

    try:
        result = asyncio.run(run())
        text = (
            getattr(result, "markdown", None)
            or getattr(result, "fit_markdown", None)
            or getattr(result, "cleaned_html", None)
            or getattr(result, "html", None)
            or ""
        )
        metadata = getattr(result, "metadata", {})
        title = metadata.get("title", "") if isinstance(metadata, dict) else ""
        if text:
            return title or url, text
    except Exception:
        return None
    return None


def _scrape_with_playwright(url: str) -> tuple[str, str] | None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    try:
        with sync_playwright() as playwright:
            chrome_path = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
            launch_options = {"headless": True}
            if chrome_path.exists():
                launch_options["executable_path"] = str(chrome_path)
            browser = playwright.chromium.launch(**launch_options)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=15000)
            title = page.title() or url
            text = page.locator("body").inner_text(timeout=5000)
            browser.close()
        if text:
            return title, text
    except Exception:
        return None
    return None


def _scrape_with_scrapy(raw: str, url: str) -> tuple[str, str] | None:
    try:
        from scrapy import Selector
    except Exception:
        return None

    try:
        selector = Selector(text=raw)
        title = _squash(" ".join(selector.css("title::text").getall())) or url
        parts = selector.css("p::text, li::text, h1::text, h2::text, h3::text, article *::text").getall()
        body = _squash(" ".join(parts))
        if body:
            return title, body
    except Exception:
        return None
    return None


def _free_scrape_url(url: str, prefer_browser: bool = False) -> tuple[str, str, str] | None:
    url = _squash(url)
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = "https://" + url

    crawl4ai_result = _scrape_with_crawl4ai(url)
    if crawl4ai_result:
        return crawl4ai_result[0], crawl4ai_result[1], "Crawl4AI"

    if prefer_browser:
        playwright_result = _scrape_with_playwright(url)
        if playwright_result:
            return playwright_result[0], playwright_result[1], "Playwright"

    try:
        try:
            import requests

            response = requests.get(url, headers={"User-Agent": "JarvisLocalCore/1.0"}, timeout=15)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            raw = response.content[:1_500_000]
        except Exception:
            request = urllib.request.Request(url, headers={"User-Agent": "JarvisLocalCore/1.0"})
            with urllib.request.urlopen(request, timeout=15) as response:
                content_type = response.headers.get("Content-Type", "")
                raw = response.read(1_500_000)
        if "text" not in content_type and "html" not in content_type and not raw.strip().startswith(b"<"):
            return url, "I opened the link, but it is not readable text.", "urllib"
        html_text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return None

    bs_result = _scrape_with_beautifulsoup(html_text, url)
    if bs_result:
        return bs_result[0], bs_result[1], "requests + BeautifulSoup"

    scrapy_result = _scrape_with_scrapy(html_text, url)
    if scrapy_result:
        return scrapy_result[0], scrapy_result[1], "Scrapy Selector"

    title, body = _extract_text_from_html(html_text, url)
    return title, body, "stdlib HTML parser"


def _crawl_command(command: str) -> str | None:
    normalized = _normalized(command)
    if not re.search(r"\b(crawl|scrape|extract|read website|read page|summarize website)\b", normalized):
        return None

    match = re.search(r"https?://\S+|(?:www\.)\S+\.\S+", command, re.IGNORECASE)
    if not match:
        return "Give me a URL to crawl or scrape."

    url = match.group(0).rstrip(").,;")
    prefer_browser = any(word in normalized for word in ["playwright", "browser", "dynamic", "javascript"])
    result = _free_scrape_url(url, prefer_browser=prefer_browser)
    if not result:
        return "I could not crawl that URL with the local free scraper stack."
    title, body, engine = result
    return _summarize_scraped_text(title, body, url, engine)


def _wikipedia_summary(topic: str) -> str:
    topic = _squash(topic)
    if not topic:
        return "Tell me the Wikipedia topic."

    def fetch_page(title_text: str) -> str:
        title = urllib.parse.quote(title_text.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        request = urllib.request.Request(url, headers={"User-Agent": "JarvisLocalCore/1.0"})
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        return _squash(data.get("extract", ""))

    try:
        extract = fetch_page(topic)
        if not extract:
            return f"I could not find a readable Wikipedia summary for {topic}."
        return extract
    except Exception:
        pass

    try:
        query = urllib.parse.urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "srlimit": "1",
                "format": "json",
                "utf8": "1",
            }
        )
        url = f"https://en.wikipedia.org/w/api.php?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": "JarvisLocalCore/1.0"})
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = data.get("query", {}).get("search", [])
        if results:
            extract = fetch_page(results[0].get("title", topic))
            if extract:
                return extract
    except Exception:
        pass

    return f"I could not fetch Wikipedia results for {topic}."


def _clean_general_topic(topic: str) -> str:
    topic = re.sub(
        r"\b(for me|to me|please|in short|briefly|in detail|full details|give answer|answer me)\b",
        " ",
        topic,
        flags=re.IGNORECASE,
    )
    topic = topic.strip(" ?!.,:;\"'")
    return _squash(topic)


def _extract_general_topic(command: str) -> str:
    text = _squash(command).strip()
    if not text:
        return ""

    if re.match(r"^(help|what can you do|what can jarvis do)\b", text, flags=re.IGNORECASE):
        return ""

    patterns = [
        r"^(?:please\s+)?(?:tell|teach|explain)\s+(?:me\s+)?(?:about\s+)?(.+)$",
        r"^(?:please\s+)?(?:what|who|where)\s+(?:is|are|was|were)\s+(.+)$",
        r"^(?:please\s+)?(?:give|show)\s+(?:me\s+)?(?:information|details|info)\s+(?:about|on|of)\s+(.+)$",
        r"^(?:please\s+)?(?:information|details|info)\s+(?:about|on|of)\s+(.+)$",
        r"^(?:please\s+)?(?:about|define|describe)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_general_topic(match.group(1))

    normalized = _normalized(text)
    command_words = (
        "open",
        "search",
        "google",
        "write",
        "draft",
        "save",
        "note",
        "email",
        "send",
        "share",
        "play",
        "scroll",
        "terminal",
        "run",
        "train",
        "learn",
        "news",
        "briefing",
        "shutdown",
        "calculate",
        "calculator",
        "read file",
        "write file",
    )
    if len(text.split()) <= 8 and not any(word in normalized for word in command_words):
        return _clean_general_topic(text)

    return ""


def _answer_general_question(command: str) -> str | None:
    if _is_identity_question(command):
        return _jarvis_identity_answer()

    topic = _extract_general_topic(command)
    if not topic:
        return None

    rag_result = answer_with_rag(topic)
    non_skill_matches = [
        item for item in rag_result.get("matches", [])
        if not str(item.get("source", "")).startswith("jarvis-skill:")
    ]
    if non_skill_matches:
        sources = []
        context = "\n\n".join(f"{item.get('title', 'Knowledge')}: {item.get('text', '')}" for item in non_skill_matches[:3])
        answer = _polish_answer_from_context(topic, context, max_words=155)
        for item in non_skill_matches[:3]:
            source = item.get("source") or item.get("title") or "memory"
            if str(source).lower().startswith("github readme:"):
                source = str(source).split(":", 1)[1].strip()
            if source not in sources:
                sources.append(source)
        visible_sources = [source for source in sources if not str(source).startswith("jarvis-skill:")]
        source_text = "\n\nSources: " + "; ".join(visible_sources) if visible_sources else ""
        return (
            answer
            + source_text
        )

    live_results = _open_source_search(topic, max_results=5)
    if live_results:
        return _format_open_source_search_answer(topic, live_results)

    summary = _wikipedia_summary(topic)
    if not summary.startswith("I could not"):
        return (
            f"{topic}:\n\n{summary}"
        )

    api_message = _api_reply(command)
    if api_message:
        return api_message

    ollama_message = _ollama_reply(command)
    if ollama_message:
        return ollama_message

    return (
        f"I could not fetch a verified answer for {topic} right now. "
        f"Ask me to search {topic}, or start Jarvis with internet access for live retrieval."
    )


def _detect_code_language(command: str) -> str:
    normalized = _normalized(command)
    if re.search(r"\b(nextjs|next\.js|next)\b", normalized):
        return "tsx"
    if re.search(r"\breact\b", normalized):
        return "jsx"
    if any(word in normalized for word in ["website", "web site", "webpage", "web page", "site", "frontend", "landing page"]):
        return "html"
    for language in ["python", "javascript", "typescript", "html", "css", "java", "c++", "cpp", "c#", "csharp", "php", "sql"]:
        if language in normalized:
            return "cpp" if language == "c++" else ("csharp" if language == "c#" else language)
    if "name fixer" in normalized:
        return "html"
    return "python"


def _website_name_fixer_code() -> str:
    return '''```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Name Fixer</title>
    <style>
      :root {
        color-scheme: light;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
        color: #17202a;
        background: #f4f6f8;
      }

      main {
        width: min(760px, 100%);
        display: grid;
        gap: 18px;
      }

      .panel {
        padding: 22px;
        border: 1px solid #dde3ea;
        border-radius: 14px;
        background: white;
        box-shadow: 0 20px 48px rgba(31, 41, 55, 0.08);
      }

      h1 { margin: 0 0 6px; font-size: clamp(2rem, 6vw, 3.5rem); }
      p { margin: 0; color: #667085; line-height: 1.5; }

      textarea {
        width: 100%;
        min-height: 132px;
        margin-top: 14px;
        padding: 14px;
        border: 1px solid #ccd5df;
        border-radius: 10px;
        resize: vertical;
        font: inherit;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 12px;
      }

      button {
        min-height: 40px;
        padding: 10px 14px;
        border: 0;
        border-radius: 10px;
        color: white;
        background: #1473e6;
        cursor: pointer;
        font-weight: 700;
      }

      button.secondary { color: #17202a; background: #edf2f7; }

      .results {
        display: grid;
        gap: 10px;
      }

      .result {
        display: grid;
        gap: 4px;
        padding: 14px;
        border: 1px solid #e4e7ec;
        border-radius: 10px;
        background: #fbfcfd;
      }

      .result span { color: #667085; font-size: 0.85rem; font-weight: 700; }
      .result strong { overflow-wrap: anywhere; }
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <h1>Name Fixer</h1>
        <p>Paste a messy name and get clean title case, initials, username, slug, and file-safe output.</p>
        <textarea id="nameInput" placeholder="Example:   md    WASI__portfolio site  "></textarea>
        <div class="actions">
          <button id="fixBtn">Fix name</button>
          <button id="copyBtn" class="secondary">Copy best result</button>
          <button id="clearBtn" class="secondary">Clear</button>
        </div>
      </section>

      <section class="panel results" id="results" aria-live="polite"></section>
    </main>

    <script>
      const input = document.querySelector("#nameInput");
      const results = document.querySelector("#results");
      const fixBtn = document.querySelector("#fixBtn");
      const copyBtn = document.querySelector("#copyBtn");
      const clearBtn = document.querySelector("#clearBtn");

      function cleanWords(value) {
        return value
          .replace(/[_-]+/g, " ")
          .replace(/[^a-zA-Z0-9 ]+/g, "")
          .trim()
          .split(/\\s+/)
          .filter(Boolean);
      }

      function titleCase(words) {
        return words.map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(" ");
      }

      function render() {
        const words = cleanWords(input.value);
        if (!words.length) {
          results.innerHTML = '<p>Type a name to fix it.</p>';
          return;
        }

        const title = titleCase(words);
        const slug = words.map((word) => word.toLowerCase()).join("-");
        const username = words.map((word) => word.toLowerCase()).join("");
        const initials = words.map((word) => word[0].toUpperCase()).join("");
        const fileSafe = slug.replace(/-+/g, "-");

        const rows = [
          ["Best display name", title],
          ["Initials", initials],
          ["Username", username],
          ["Website slug", slug],
          ["File-safe name", fileSafe],
        ];

        results.innerHTML = rows.map(([label, value]) => `
          <div class="result">
            <span>${label}</span>
            <strong>${value}</strong>
          </div>
        `).join("");
      }

      fixBtn.addEventListener("click", render);
      input.addEventListener("input", render);
      copyBtn.addEventListener("click", async () => {
        const best = results.querySelector("strong")?.textContent || "";
        if (best) await navigator.clipboard.writeText(best);
      });
      clearBtn.addEventListener("click", () => {
        input.value = "";
        render();
      });

      render();
    </script>
  </body>
</html>
```'''


def _title_from_prompt(command: str, fallback: str = "Jarvis Website") -> str:
    cleaned = re.sub(
        r"\b(write|create|generate|make|code|program|script|for|a|an|my|the|using|with|in|html|css|javascript|js|react|nextjs|next\.js|next|python|website|webpage|web page|web site|site|app|improved|polished|responsive|version)\b",
        " ",
        _normalized(command),
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", cleaned)
    words = [word for word in cleaned.split() if word][:4]
    return " ".join(word.capitalize() for word in words) if words else fallback


def _simple_website_code(title: str, subtitle: str, kind: str = "generic") -> str:
    if kind == "task":
        body = '<input id="itemInput" placeholder="Add a task"><button id="addBtn">Add task</button><ul id="list"></ul>'
        script = 'const input=document.querySelector("#itemInput");const list=document.querySelector("#list");document.querySelector("#addBtn").onclick=()=>{if(!input.value.trim())return;const item=document.createElement("li");item.textContent=input.value;item.onclick=()=>item.classList.toggle("done");list.appendChild(item);input.value="";};'
    elif kind == "login":
        body = '<input placeholder="Email"><input type="password" placeholder="Password"><button>Sign in</button>'
        script = ""
    elif kind == "portfolio":
        body = '<div class="grid"><article><span>Project</span><strong>Jarvis Assistant</strong><p>Secure desktop automation, code writing, and daily briefing tools.</p></article><article><span>Skill</span><strong>Frontend + AI</strong><p>Responsive UI, local actions, and safe approval flows.</p></article><article><span>Contact</span><strong>hello@example.com</strong><p>Replace this with your real contact details.</p></article></div>'
        script = 'document.querySelectorAll("article").forEach((card)=>card.addEventListener("click",()=>card.classList.toggle("selected")));'
    else:
        body = '<div class="grid"><article><span>Feature</span><strong>Fast</strong><p>Designed to load quickly and work on mobile.</p></article><article><span>Feature</span><strong>Responsive</strong><p>The layout adapts across screen sizes.</p></article><article><span>Feature</span><strong>Ready</strong><p>Edit the content and connect your own logic.</p></article></div>'
        script = 'document.querySelectorAll("article").forEach((card)=>card.addEventListener("click",()=>card.classList.toggle("selected")));'

    return f'''```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px; font-family: Inter, system-ui, sans-serif; color: #17202a; background: #f4f6f8; }}
      main {{ width: min(760px, 100%); display: grid; gap: 18px; }}
      .panel {{ padding: 22px; border: 1px solid #dde3ea; border-radius: 14px; background: white; box-shadow: 0 20px 48px rgba(31, 41, 55, 0.08); }}
      h1 {{ margin: 0 0 6px; font-size: clamp(2rem, 6vw, 3.5rem); }}
      p {{ margin: 0; color: #667085; line-height: 1.5; }}
      input, textarea {{ width: 100%; min-height: 44px; margin-top: 14px; padding: 12px; border: 1px solid #ccd5df; border-radius: 10px; font: inherit; }}
      button {{ min-height: 40px; margin-top: 12px; padding: 10px 14px; border: 0; border-radius: 10px; color: white; background: #1473e6; cursor: pointer; font-weight: 700; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 16px; }}
      li, article {{ display: grid; gap: 4px; padding: 14px; border: 1px solid #e4e7ec; border-radius: 10px; background: #fbfcfd; }}
      ul {{ display: grid; gap: 10px; padding: 0; list-style: none; }}
      .done {{ text-decoration: line-through; opacity: .55; }}
      .selected {{ border-color: #1473e6; box-shadow: 0 0 0 3px rgba(20, 115, 230, .12); }}
      article span {{ color: #667085; font-size: .85rem; font-weight: 700; }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <h1>{html.escape(title)}</h1>
        <p>{html.escape(subtitle)}</p>
        {body}
      </section>
    </main>
    <script>{script}</script>
  </body>
</html>
```'''


def _react_code(title: str, kind: str = "generic", nextjs: bool = False) -> str:
    fence = "tsx" if nextjs else "jsx"
    prelude = '"use client";\n\n' if nextjs else ""
    component = re.sub(r"[^a-zA-Z0-9]+", " ", title).title().replace(" ", "") or "GeneratedApp"
    if kind == "task":
        return f'''```{fence}
{prelude}import {{ useMemo, useState }} from "react";

export default function TaskManager() {{
  const [items, setItems] = useState([]);
  const [text, setText] = useState("");
  const completed = useMemo(() => items.filter((item) => item.done).length, [items]);

  function addTask(event) {{
    event.preventDefault();
    if (!text.trim()) return;
    setItems([...items, {{ id: crypto.randomUUID(), title: text.trim(), done: false }}]);
    setText("");
  }}

  return (
    <main className="min-h-screen bg-slate-100 p-6 text-slate-950">
      <section className="mx-auto grid max-w-2xl gap-4 rounded-2xl bg-white p-6 shadow-xl">
        <h1 className="text-4xl font-bold">Task Manager</h1>
        <p className="text-slate-500">{{completed}} of {{items.length}} completed</p>
        <form onSubmit={{addTask}} className="flex gap-2">
          <input className="min-w-0 flex-1 rounded-xl border p-3" value={{text}} onChange={{(event) => setText(event.target.value)}} placeholder="Add a task" />
          <button className="rounded-xl bg-blue-600 px-4 font-bold text-white">Add</button>
        </form>
        {{items.map((item) => (
          <button key={{item.id}} onClick={{() => setItems(items.map((task) => task.id === item.id ? {{ ...task, done: !task.done }} : task))}} className="rounded-xl bg-slate-50 p-3 text-left">
            <span className={{item.done ? "line-through opacity-50" : ""}}>{{item.title}}</span>
          </button>
        ))}}
      </section>
    </main>
  );
}}
```'''
    return f'''```{fence}
{prelude}import {{ useMemo, useState }} from "react";

export default function {component}() {{
  const [value, setValue] = useState("");
  const output = useMemo(() => value.trim() || "Start typing to generate a result.", [value]);

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-100 p-6 text-zinc-950">
      <section className="grid w-full max-w-3xl gap-5 rounded-2xl bg-white p-6 shadow-xl">
        <h1 className="text-4xl font-bold">{html.escape(title)}</h1>
        <p className="text-zinc-500">Responsive app generated from your prompt.</p>
        <textarea className="min-h-32 rounded-xl border p-4" value={{value}} onChange={{(event) => setValue(event.target.value)}} placeholder="Type here" />
        <article className="rounded-xl bg-zinc-50 p-4">{{output}}</article>
      </section>
    </main>
  );
}}
```'''


def _rag_prefix_for_prompt(command: str, route: dict) -> str:
    return ""


def _code_from_prompt(command: str) -> str:
    api_message = _api_reply(command)
    if api_message:
        return api_message

    route = _route_command(command)
    prefix = _rag_prefix_for_prompt(command, route)
    language = _detect_code_language(command)
    task = re.sub(r"\b(write|create|generate|make|code|program|script|in|using|with)\b", " ", command, flags=re.IGNORECASE)
    task = _squash(task) or "the requested task"
    normalized = _normalized(command)
    is_name_fixer = "name fixer" in normalized
    is_todo = bool(re.search(r"\b(todo|task manager|task app)\b", normalized))
    is_portfolio = bool(re.search(r"\b(portfolio|personal website)\b", normalized))
    is_login = bool(re.search(r"\b(login|sign in|signin)\b", normalized))
    is_calculator = "calculator" in normalized
    title = "Name Fixer" if is_name_fixer else "Task Manager" if is_todo else "Portfolio" if is_portfolio else "Login Portal" if is_login else "Calculator" if is_calculator else _title_from_prompt(command)
    kind = "task" if is_todo else "portfolio" if is_portfolio else "login" if is_login else "name" if is_name_fixer else "generic"

    if language == "html" and is_name_fixer:
        return prefix + _website_name_fixer_code()

    if language == "html" and not is_calculator:
        return prefix + _simple_website_code(title, f"A responsive {title} website generated from your prompt.", kind)

    if language in {"jsx", "tsx"}:
        return prefix + _react_code(title, kind, nextjs=language == "tsx")

    if language == "python" and is_name_fixer:
        return prefix + '''```python
import re


def fix_name(value: str) -> dict[str, str]:
    words = re.sub(r"[_-]+", " ", value)
    words = re.sub(r"[^a-zA-Z0-9 ]+", "", words).strip().split()
    return {
        "display_name": " ".join(word.capitalize() for word in words),
        "initials": "".join(word[0].upper() for word in words),
        "username": "".join(word.lower() for word in words),
        "slug": "-".join(word.lower() for word in words),
    }


if __name__ == "__main__":
    raw = input("Enter messy name: ")
    for key, value in fix_name(raw).items():
        print(f"{key}: {value}")
```'''

    if language == "python" and is_todo:
        return prefix + '''```python
from dataclasses import dataclass


@dataclass
class Task:
    title: str
    done: bool = False


class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    def add(self, title: str) -> None:
        if title.strip():
            self.tasks.append(Task(title.strip()))

    def complete(self, index: int) -> None:
        self.tasks[index].done = True

    def list_tasks(self) -> list[str]:
        return [f"{index}. [{'done' if task.done else 'open'}] {task.title}" for index, task in enumerate(self.tasks, 1)]


if __name__ == "__main__":
    manager = TaskManager()
    manager.add("Build Jarvis")
    manager.add("Test code writer")
    manager.complete(0)
    print("\\n".join(manager.list_tasks()))
```'''

    if is_calculator and language in {"html", "javascript", "typescript"}:
        return prefix + '''```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Calculator</title>
    <style>
      body { margin: 0; min-height: 100vh; display: grid; place-items: center; font-family: system-ui, sans-serif; background: #101820; color: white; }
      .calculator { width: min(340px, 92vw); padding: 16px; border-radius: 12px; background: #17232e; box-shadow: 0 20px 50px #0008; }
      #display { width: 100%; height: 58px; margin-bottom: 12px; padding: 0 12px; border: 0; border-radius: 8px; text-align: right; font-size: 1.7rem; background: #0b1117; color: white; }
      .keys { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
      button { min-height: 52px; border: 0; border-radius: 8px; font-size: 1.1rem; background: #223240; color: white; cursor: pointer; }
      button.operator { background: #29b6f6; color: #071016; font-weight: 700; }
      button.danger { background: #ff6b7a; color: #071016; font-weight: 700; }
    </style>
  </head>
  <body>
    <main class="calculator">
      <input id="display" readonly value="0" aria-label="Calculator display">
      <section class="keys">
        <button class="danger" data-action="clear">C</button><button data-value="(">(</button><button data-value=")">)</button><button class="operator" data-value="/">/</button>
        <button data-value="7">7</button><button data-value="8">8</button><button data-value="9">9</button><button class="operator" data-value="*">*</button>
        <button data-value="4">4</button><button data-value="5">5</button><button data-value="6">6</button><button class="operator" data-value="-">-</button>
        <button data-value="1">1</button><button data-value="2">2</button><button data-value="3">3</button><button class="operator" data-value="+">+</button>
        <button data-value="0">0</button><button data-value=".">.</button><button data-action="backspace">⌫</button><button class="operator" data-action="equals">=</button>
      </section>
    </main>
    <script>
      const display = document.querySelector("#display");
      document.querySelector(".keys").addEventListener("click", (event) => {
        const button = event.target.closest("button");
        if (!button) return;
        if (button.dataset.action === "clear") display.value = "0";
        else if (button.dataset.action === "backspace") display.value = display.value.length > 1 ? display.value.slice(0, -1) : "0";
        else if (button.dataset.action === "equals") {
          if (/^[0-9+\\-*/().\\s]+$/.test(display.value)) display.value = String(Function(`return ${display.value}`)());
        } else display.value = display.value === "0" ? button.dataset.value : display.value + button.dataset.value;
      });
    </script>
  </body>
</html>
```'''

    if "calculator" in _normalized(command) and language == "python":
        return prefix + '''```python
import tkinter as tk


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.resizable(False, False)
        self.expression = tk.StringVar(value="0")
        tk.Entry(self, textvariable=self.expression, justify="right", font=("Segoe UI", 20), width=18).grid(row=0, column=0, columnspan=4, padx=8, pady=8)
        buttons = [
            ("C", 1, 0), ("(", 1, 1), (")", 1, 2), ("/", 1, 3),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("*", 2, 3),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("-", 3, 3),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("+", 4, 3),
            ("0", 5, 0), (".", 5, 1), ("⌫", 5, 2), ("=", 5, 3),
        ]
        for text, row, column in buttons:
            tk.Button(self, text=text, width=5, height=2, font=("Segoe UI", 14), command=lambda value=text: self.press(value)).grid(row=row, column=column, padx=4, pady=4)

    def press(self, value):
        current = self.expression.get()
        if value == "C":
            self.expression.set("0")
        elif value == "⌫":
            self.expression.set(current[:-1] or "0")
        elif value == "=":
            if all(char in "0123456789+-*/(). " for char in current):
                try:
                    self.expression.set(str(eval(current, {"__builtins__": {}}, {})))
                except Exception:
                    self.expression.set("Error")
        else:
            self.expression.set(value if current in {"0", "Error"} else current + value)


if __name__ == "__main__":
    Calculator().mainloop()
```'''

    templates = {
        "python": f'''```python
def process_text(value: str) -> str:
    """Clean spacing and return a simple processed result."""
    return " ".join(value.strip().split())


def main():
    raw = input("Enter text for {task}: ")
    print(process_text(raw))


if __name__ == "__main__":
    main()
```''',
        "javascript": f'''```javascript
function processText(value) {{
  return value.trim().replace(/\\s+/g, " ");
}}

function main() {{
  const result = processText("  Example input for {task}  ");
  console.log(result);
}}

main();
```''',
        "typescript": f'''```typescript
function processText(value: string): string {{
  return value.trim().replace(/\\s+/g, " ");
}}

function main(): void {{
  const result = processText("  Example input for {task}  ");
  console.log(result);
}}

main();
```''',
        "html": f'''```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(task.title())}</title>
  </head>
  <body>
    <main>
      <h1>{html.escape(task.title())}</h1>
    </main>
  </body>
</html>
```''',
        "css": f'''```css
:root {{
  color-scheme: dark;
  font-family: system-ui, sans-serif;
}}

.app {{
  display: grid;
  gap: 1rem;
}}
```''',
        "java": f'''```java
public class Main {{
    static String processText(String value) {{
        return value.trim().replaceAll("\\\\s+", " ");
    }}

    public static void main(String[] args) {{
        System.out.println(processText("  Example input for {task}  "));
    }}
}}
```''',
        "cpp": f'''```cpp
#include <iostream>
#include <regex>
#include <string>

int main() {{
    std::string value = "  Example input for {task}  ";
    value = std::regex_replace(value, std::regex("\\\\s+"), " ");
    std::cout << value << "\\n";
    return 0;
}}
```''',
        "csharp": f'''```csharp
using System;
using System.Text.RegularExpressions;

class Program {{
    static void Main() {{
        string value = "  Example input for {task}  ".Trim();
        Console.WriteLine(Regex.Replace(value, "\\\\s+", " "));
    }}
}}
```''',
        "php": f'''```php
<?php
$value = trim("  Example input for {task}  ");
echo preg_replace('/\\s+/', ' ', $value) . "\\n";
?>
```''',
        "sql": f'''```sql
-- Starter query for: {task}
SELECT *
FROM your_table
LIMIT 10;
```''',
    }
    return prefix + templates.get(language, templates["python"])


def _ollama_reply(command: str) -> str | None:
    global OLLAMA_UNAVAILABLE_UNTIL

    if time.time() < OLLAMA_UNAVAILABLE_UNTIL:
        return None

    settings = _load_settings()
    model = settings.get("ollama_model") or "gemma3"
    try:
        active_skill_context = skill_context(command)
    except Exception:
        active_skill_context = ""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Jarvis. Correct typos and answer with useful code or concise steps. "
                    "Use the active skill rules when provided.\n"
                    f"{active_skill_context}"
                ),
            },
            {"role": "user", "content": command},
        ],
        "stream": False,
    }
    try:
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
        return _squash(data.get("message", {}).get("content", ""))
    except Exception:
        OLLAMA_UNAVAILABLE_UNTIL = time.time() + 60
        return None


def _open_source_briefing(command: str = "") -> dict | None:
    normalized = _normalized(command)
    categories = [
        ("Business", r"\b(business|finance|financial|market|markets|stock|stocks|economy|economic)\b", "latest business finance markets economy news"),
        ("Sports", r"\b(sport|sports|cricket|football|ipl|nba|tennis)\b", "latest sports cricket football news"),
        ("AI", r"\b(ai|artificial intelligence|machine learning|deepseek|chatgpt|llm)\b", "latest artificial intelligence AI LLM news"),
        ("Technology", r"\b(technology|tech|startup|software|gadget)\b", "latest technology startup software news"),
        ("India", r"\b(india|indian|bharat)\b", "latest India news"),
        ("World", r"\b(world|international|global)\b", "latest world international news"),
        ("Science", r"\b(science|space|research)\b", "latest science space research news"),
        ("Health", r"\b(health|medical|medicine)\b", "latest health medical news"),
        ("Education", r"\b(education|university|college|school)\b", "latest education university news"),
    ]
    selected = [(label, query) for label, pattern, query in categories if re.search(pattern, normalized)]
    if not selected:
        selected = [
            ("Top India", "latest important India news"),
            ("Business", "latest business finance markets news"),
            ("Sports", "latest sports cricket news"),
            ("AI", "latest artificial intelligence AI news"),
            ("Technology", "latest technology news"),
        ]

    sections = []
    for label, query in selected[:5]:
        data = _open_source_search(query, topic="news", max_results=3)
        if not data:
            continue
        items = []
        for result in data.get("results", [])[:3]:
            title = _squash(result.get("title", ""))
            if not title:
                continue
            items.append(
                {
                    "title": title,
                    "summary": _squash(result.get("content", ""))[:220],
                    "link": _squash(result.get("url", "")),
                    "published": _squash(result.get("published", "")),
                    "source": _squash(result.get("source", "")) or _source_name_from_url(result.get("url", "")),
                }
            )
        if items:
            sections.append(
                {
                    "name": label,
                    "items": items,
                    "answer": _squash(data.get("answer", "")),
                    "provider": data.get("provider", "free search"),
                }
            )

    if not sections:
        return None

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    section_label = sections[0]["name"] if len(sections) == 1 else "news"
    lines = [
        f"Latest {section_label} briefing for {datetime.datetime.now().strftime('%A, %B %d, %Y')} ({today}).",
    ]
    for section in sections:
        lines.append("")
        lines.append(f"{section['name']}:")
        if section.get("answer"):
            lines.append("")
            lines.append(section["answer"])
        lines.append("")
        for item in section["items"][:3]:
            source = f" ({item['source']})" if item.get("source") else ""
            published = f" - {item['published']}" if item.get("published") else ""
            link = f" - {item['link']}" if item.get("link") else ""
            lines.append(f"- {item['title']}{source}{published}{link}")

    return {"message": "\n".join(lines), "sections": sections, "provider": "free-open-source"}


def _daily_briefing(command: str = "") -> dict:
    briefing = _open_source_briefing(command)
    if briefing:
        return briefing

    status = _search_stack_status()
    available = ", ".join(name for name, ok in status.items() if isinstance(ok, bool) and ok) or "none"
    message = (
        "I could not fetch live news through the free local search stack right now. "
        f"Available local pieces: {available}. Check the internet connection or add a self-hosted SearXNG URL in Settings."
    )
    return {"message": message, "sections": [], "provider": "free-open-source"}


def _api_reply(command: str) -> str | None:
    settings = _load_settings()
    if not settings.get("api_enabled") or not settings.get("api_key"):
        return None

    try:
        active_skill_context = skill_context(command)
    except Exception:
        active_skill_context = ""
    payload = {
        "model": settings.get("api_model") or "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Jarvis, a secure desktop assistant. Correct obvious typos, "
                    "answer concisely, and never claim an action was completed unless a tool did it. "
                    "Use the active skill rules when provided.\n"
                    f"{active_skill_context}"
                ),
            },
            {"role": "user", "content": command},
        ],
        "temperature": 0.35,
    }

    try:
        request = urllib.request.Request(
            settings.get("api_endpoint") or DEFAULT_SETTINGS["api_endpoint"],
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings['api_key']}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _write_note(content: str) -> str:
    content = _squash(content)
    if not content:
        return "Tell me what to write."

    _ensure_data_dirs()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    with NOTES_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[{stamp}] {content}\n")
    return "Note saved."


def _read_notes() -> str:
    if not NOTES_FILE.exists():
        return "There are no saved notes yet."

    notes = NOTES_FILE.read_text(encoding="utf-8").strip()
    if not notes:
        return "There are no saved notes yet."

    lines = notes.splitlines()[-5:]
    return "Here are the latest notes. " + " ".join(lines)


def _write_file(command: str) -> str:
    match = re.search(r"write\s+file\s+(.+?)\s+(?:content|body|text)\s+(.+)$", command, re.IGNORECASE)
    if not match:
        return "Use: write file filename.txt content your text."

    filename = _safe_filename(match.group(1))
    content = match.group(2).strip()
    _ensure_data_dirs()
    target = FILES_DIR / filename
    target.write_text(content, encoding="utf-8")
    return f"Wrote {filename}."


def _read_file(command: str) -> str:
    match = re.search(r"read\s+file\s+(.+)$", command, re.IGNORECASE)
    if not match:
        return "Tell me which file to read."

    filename = _safe_filename(match.group(1))
    target = FILES_DIR / filename
    if not target.exists():
        return f"I could not find {filename} in Jarvis files."

    content = target.read_text(encoding="utf-8").strip()
    if not content:
        return f"{filename} is empty."
    return content[:1200]


def _train_local_brain() -> str:
    skill_stats = install_default_skills(add_knowledge=add_knowledge, add_intent_example=add_intent_example)
    stats = train_intent_model()
    labels = ", ".join(stats.get("labels", []))
    return (
        "Local brain trained. "
        f"Examples: {stats.get('rows', 0)}. "
        f"Words learned: {stats.get('vocab_size', 0)}. "
        f"Engine: {stats.get('backend', 'local')}. "
        f"Skill packs: {skill_stats.get('total', 0)} total, {skill_stats.get('installed', 0)} newly installed. "
        f"Intents: {labels}."
    )


def _skill_command_from_command(command: str) -> str | None:
    normalized = _normalized(command)

    if normalized in {"train skills", "install skills", "train skill pack", "train skill packs", "install skill pack", "install skill packs"}:
        result = install_default_skills(add_knowledge=add_knowledge, add_intent_example=add_intent_example)
        train_intent_model()
        return (
            "Skill packs installed into Jarvis brain. "
            f"Total skills: {result.get('total', 0)}. "
            f"New skills: {result.get('installed', 0)}. "
            "Skills now guide coding, answering, message writing, news, RAG, desktop control, and security."
        )

    if normalized in {"retrain skills", "refresh skills", "retrain skill pack", "refresh skill pack"}:
        result = install_default_skills(add_knowledge=add_knowledge, add_intent_example=add_intent_example, force=True)
        train_intent_model()
        return (
            "Skill packs refreshed and saved into RAG memory. "
            f"Total skills: {result.get('total', 0)}. "
            f"Updated skills: {result.get('installed', 0)}."
        )

    if normalized in {"skill status", "skills status", "list skills", "show skills", "what skills do you have"}:
        status = skill_status()
        if status.get("total", 0) <= 0:
            return "No skill packs are installed yet. Say: train skills."
        categories = ", ".join(f"{name}: {count}" for name, count in status.get("categories", {}).items())
        names = ", ".join(item.get("title", "") for item in status.get("skills", [])[:10])
        return (
            f"Jarvis has {status.get('total', 0)} skill packs installed. "
            f"Categories: {categories}. "
            f"Skills: {names}."
        )

    return None


def _learn_intent_from_command(command: str) -> str | None:
    match = re.search(r"^learn\s+intent\s+(.+?)\s+as\s+([a-zA-Z_ -]+)$", command, re.IGNORECASE)
    if not match:
        match = re.search(r"^train\s+intent\s+(.+?)\s+as\s+([a-zA-Z_ -]+)$", command, re.IGNORECASE)
    if not match:
        return None

    example = _squash(match.group(1).strip(" \"'"))
    intent = re.sub(r"[^a-z0-9_]+", "_", match.group(2).lower()).strip("_")
    if not example or not intent:
        return "Use: learn intent <example command> as <intent_name>."

    stats = add_intent_example(example, intent)
    return (
        f"Learned intent example. '{example}' now trains '{intent}'. "
        f"Model examples: {stats.get('rows', 0)}."
    )


def _knowledge_link_from_command(command: str) -> str | None:
    normalized = _normalized(command)
    if not any(phrase in normalized for phrase in ["add link", "learn link", "train from link", "add url", "learn url"]):
        return None

    match = re.search(r"https?://\S+|(?:www\.)\S+\.\S+", command, re.IGNORECASE)
    if not match:
        return "Give me the link to learn from."

    url = match.group(0).rstrip(").,;")
    try:
        if "github.com" in url.lower() or "raw.githubusercontent.com" in url.lower():
            result = import_dataset(url)
        else:
            result = add_link(url)
    except Exception as error:
        return f"I could not learn that link yet: {error}"

    if result.get("chunks_added", 0) <= 0:
        return result.get("message") or "I opened the link but could not find readable text to save."
    return (
        f"Knowledge saved from link. Chunks added: {result.get('chunks_added', 0)}. "
        f"Total memory chunks: {result.get('total_chunks', 0)}."
    )


def _knowledge_text_from_command(command: str) -> str | None:
    patterns = [
        r"^add\s+knowledge\s+(.+)$",
        r"^learn\s+knowledge\s+(.+)$",
        r"^remember\s+knowledge\s+(.+)$",
        r"^train\s+from\s+text\s+(.+)$",
        r"^learn\s+this\s+(.+)$",
    ]
    text = ""
    for pattern in patterns:
        match = re.search(pattern, command, re.IGNORECASE | re.DOTALL)
        if match:
            text = _squash(match.group(1))
            break

    if not text:
        return None
    if len(text) < 20:
        return "Give me a little more text to save into knowledge."

    title = "Manual lesson"
    title_match = re.search(r"^title\s+(.+?)\s+text\s+(.+)$", text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = _squash(title_match.group(1))
        text = _squash(title_match.group(2))

    result = add_knowledge(title, text)
    return (
        f"Knowledge saved. Chunks added: {result.get('chunks_added', 0)}. "
        f"Total memory chunks: {result.get('total_chunks', 0)}."
    )


def _dataset_from_command(command: str) -> str | None:
    patterns = [
        r"^(?:train|learn)\s+from\s+dataset\s+(.+)$",
        r"^(?:add|import)\s+dataset\s+(.+)$",
        r"^(?:train|learn)\s+from\s+kaggle\s+(.+)$",
        r"^kaggle\s+dataset\s+(.+)$",
        r"^(?:train|learn)\s+from\s+github\s+(.+)$",
        r"^(?:add|import|learn)\s+github\s+(.+)$",
    ]
    target = ""
    for pattern in patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            target = _squash(match.group(1))
            break

    if not target:
        return None

    try:
        result = import_dataset(target)
    except Exception as error:
        return f"I could not import that dataset yet: {error}"

    message = result.get("message")
    if message and result.get("chunks_added", 0) <= 0:
        return message

    return (
        f"Dataset learned. Files: {result.get('files', 1)}. "
        f"Chunks added: {result.get('chunks_added', 0)}. "
        f"Total memory chunks: {result.get('total_chunks', 0)}. "
        "Jarvis will use this as RAG context on matching prompts."
    )


def _knowledge_answer_from_command(command: str) -> str | None:
    patterns = [
        r"^(?:ask|query)\s+(?:knowledge|brain|rag)\s+(.+)$",
        r"^(?:knowledge|brain|rag)\s+question\s+(.+)$",
        r"^search\s+(?:knowledge|brain|memory)\s+(.+)$",
    ]
    query = ""
    for pattern in patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            query = _squash(match.group(1))
            break

    if not query:
        return None

    result = answer_with_rag(query)
    matches = result.get("matches", [])
    if not matches:
        return result.get("answer", "I do not have enough knowledge saved yet.")

    sources = []
    context = "\n\n".join(
        f"{item.get('title', 'Knowledge')}: {item.get('text', '')}"
        for item in matches[:3]
        if not str(item.get("source", "")).startswith("jarvis-skill:")
    )
    for item in matches[:3]:
        source = item.get("source") or item.get("title") or "memory"
        if str(source).lower().startswith("github readme:"):
            source = str(source).split(":", 1)[1].strip()
        if source not in sources:
            sources.append(source)
    visible_sources = [source for source in sources if not str(source).startswith("jarvis-skill:")]
    source_text = "\n\nSources: " + "; ".join(visible_sources) if visible_sources else ""
    answer = _polish_answer_from_context(query, result.get("answer", ""), max_words=155)
    if not answer or answer.lower().startswith("sources:"):
        answer = _polish_answer_from_context(query, context, max_words=155)
    return answer + source_text


def _local_ai_reply(command: str) -> str:
    normalized = _normalized(command)

    if _is_identity_question(command):
        return _jarvis_identity_answer()

    if normalized.startswith(("draft ", "write ")):
        topic = re.sub(r"^(draft|write)\s+", "", command, flags=re.IGNORECASE).strip()
        if "email" in normalized:
            return (
                "Subject: Quick update\n\n"
                "Hello,\n\n"
                f"{topic or 'Here is the update you asked me to prepare.'}\n\n"
                "Best regards"
            )
        return topic or "Tell me what you want me to write."

    if normalized.startswith(("summarize ", "summary of ")):
        text = re.sub(r"^(summarize|summary of)\s+", "", command, flags=re.IGNORECASE).strip()
        if not text:
            return "Give me text to summarize."
        words = text.split()
        summary = " ".join(words[:38])
        if len(words) > 38:
            summary += "..."
        return f"Summary: {summary}"

    if normalized.startswith(("help", "what can you do")):
        return (
            "I can open apps and websites, search, play YouTube, read Wikipedia, save notes, "
            "write and read Jarvis files, train my local brain from examples and links, use RAG memory, "
            "draft email with permission, speak replies, and answer simple local prompts. "
            "For Jarvis support, use mdwasiullah445@gmail.com."
        )

    general_answer = _answer_general_question(command)
    if general_answer:
        return general_answer

    api_message = _api_reply(command)
    if api_message:
        return api_message

    return (
        "I can answer questions, search live news, write code, open apps, read links, draft email with approval, "
        "or use RAG memory. Ask naturally, for example: tell me about KIIT University."
    )


def _email_subject_for_topic(topic: str) -> str:
    normalized = _normalized(topic)
    if any(word in normalized for word in ["support", "problem", "issue", "bug", "broken", "error"]) or "not working" in normalized:
        return "Jarvis Support Request"
    if "leave" in normalized:
        return "Leave Request"
    if "delay" in normalized or "late" in normalized:
        return "Project Delay Update"
    if "job" in normalized or "inquiry" in normalized:
        return "Professional Inquiry"
    if "meeting" in normalized or "schedule" in normalized:
        return "Meeting Request"
    if "thanks" in normalized or "thank" in normalized:
        return "Thank You"
    words = [word for word in re.split(r"\s+", _squash(topic)) if word][:7]
    if not words:
        return "Message Request"
    return " ".join(word[:1].upper() + word[1:].lower() for word in words)


def _draft_email_body(topic: str, include_subject: bool = False) -> str:
    topic = _squash(topic) or "your message"
    prompt = (
        f"Write a complete professional email with a subject and body about: {topic}"
        if include_subject
        else f"Write a complete professional email body about: {topic}"
    )
    api_message = _api_reply(prompt)
    if api_message:
        return api_message
    ollama_message = _ollama_reply(prompt)
    if ollama_message:
        return ollama_message
    body = (
        "Hello,\n\n"
        f"I wanted to share a clear update regarding {topic}. "
        "Please review the details and let me know if you would like any changes or further information.\n\n"
        "I appreciate your time and will be happy to follow up with the next steps.\n\n"
        "Best regards"
    )
    if include_subject:
        return f"Subject: {_email_subject_for_topic(topic)}\n\n{body}"
    return body


def _is_email_command(command: str) -> bool:
    return bool(re.search(r"\b(send|compose|write|draft)\s+(an\s+)?email\b", command, re.IGNORECASE))


def _email_topic_from_prompt(command: str, payload: dict | None = None) -> str:
    topic_match = re.search(r"(?:about|regarding|for)\s+(.+)$", command, re.IGNORECASE)
    if topic_match:
        return _squash(topic_match.group(1))

    topic = re.sub(r"\b(send|compose|write|draft)\s+(an\s+)?email\b", " ", command, flags=re.IGNORECASE)
    if payload and payload.get("to"):
        topic = topic.replace(payload["to"], " ")
    topic = re.sub(r"\b(to|for)\b\s+\S+", " ", topic, flags=re.IGNORECASE)
    return _squash(topic)


def _is_open_command(command: str) -> bool:
    return bool(re.match(r"^(open|launch|start|run)\s+", command, re.IGNORECASE))


def _confirm_agent_workflow(command: str) -> str | None:
    global PENDING_ACTION
    if not plan_task:
        return None
    plan = plan_task(command)
    if not plan.get("actionable"):
        return None
    PENDING_ACTION = {"type": "agent_workflow", "command": command, "plan": plan}
    return _response(
        "I prepared an execution plan. Approve it and I will continue the workflow.",
        "confirm_action",
        action="agent_workflow",
        plan=plan,
    )


def _execute_agent_workflow(action: dict) -> str:
    command = _squash(action.get("command", ""))
    plan = action.get("plan", {}) if isinstance(action.get("plan"), dict) else {}
    intent = plan.get("intent", "")

    if intent == "open_app_or_site":
        return _open_target(plan.get("target") or re.sub(r"^(open|launch|start)\s+", "", command, flags=re.IGNORECASE))
    if intent == "coding" or _is_code_request(command):
        return _code_from_prompt(command)
    if intent == "research":
        if re.search(r"\b(news|briefing|latest|today|current)\b", command, re.IGNORECASE):
            return _daily_briefing(command)["message"]
        return _search_web(re.sub(r"^(search|google)\s+", "", command, flags=re.IGNORECASE).strip() or command)
    if intent == "email":
        payload = _parse_email_request(command)
        if payload.get("to") and payload.get("body"):
            PENDING_EMAIL.update(payload)
            return _send_email()
        return _draft_email_body(_email_topic_from_prompt(command, payload), include_subject=True)
    if intent == "deployment":
        return (
            "Deployment workflow planned. I can prepare git/Vercel commands, but running deploys still needs "
            "a concrete project path and command confirmation."
        )
    if intent == "document":
        return "Document workflow planned. Upload or point me to the file, then I can summarize or generate the document."
    if intent == "terminal":
        return "Terminal workflow planned. Tell me the exact command and I will show an approval card before running it."
    return _local_ai_reply(command)


def _is_code_request(command: str) -> bool:
    normalized = _normalized(command)
    has_code_phrase = any(
        phrase in normalized
        for phrase in ["write code", "create code", "generate code", "write program", "create program", "make code"]
    )
    if has_code_phrase:
        return True

    has_write_verb = bool(re.search(r"\b(write|create|generate|make|build)\b", normalized))
    has_code_term = bool(re.search(
        r"\b(code|program|script|html|css|javascript|typescript|react|nextjs|next\.js|python|java|cpp|c\+\+|c#|csharp|php|sql|website|webpage|web\s+page|web\s+site|frontend|app|calculator|name\s+fixer)\b",
        normalized,
    ))
    return has_write_verb and has_code_term


@eel.expose
def process_command(command):
    global PENDING_ACTION

    raw_text = _strip_wake_prefix(_squash(command))
    learned = _learn_alias(raw_text)
    if learned:
        return _response(learned)

    text, corrections = _correct_command(raw_text)
    normalized = text.lower()
    print(f"User said: {raw_text}")
    if corrections:
        print(f"Corrected to: {text}")

    if not text:
        return _response("Please say a command.")

    if normalized in {"confirm send email", "send it", "yes send it", "yes send email", "confirm send", "approve share", "confirm share", "approve"}:
        if PENDING_SHARE.get("target"):
            return _response(_send_share())
        if PENDING_EMAIL.get("to"):
            return _response(_send_email())
        if isinstance(PENDING_ACTION, dict):
            action = PENDING_ACTION
            PENDING_ACTION = None
            if action.get("type") == "open_target":
                return _response(_open_target(action.get("target", "")), "action", plan=action.get("plan"))
            if action.get("type") == "agent_workflow":
                return _response(_execute_agent_workflow(action), "action", plan=action.get("plan"))
        return _response(_send_email())

    if normalized in {"confirm terminal", "run terminal", "yes run command", "confirm command"}:
        return _response(_run_terminal(), "terminal")

    if normalized in {"cancel email", "no", "cancel send", "cancel share"}:
        PENDING_EMAIL.update({"to": None, "subject": None, "body": None})
        PENDING_SHARE.update({"target": None, "message": None, "number": None})
        return _response("Email canceled.")

    if normalized in {"confirm shutdown", "yes shutdown", "confirm power off"} and PENDING_ACTION == "shutdown":
        PENDING_ACTION = None
        subprocess.Popen(["shutdown", "/s", "/t", "5"])
        return _response("Shutdown started. Windows will power off in 5 seconds.")

    if normalized in {"confirm open target", "confirm open app", "confirm open", "yes open"} and isinstance(PENDING_ACTION, dict) and PENDING_ACTION.get("type") == "open_target":
        action = PENDING_ACTION
        PENDING_ACTION = None
        return _response(_open_target(action.get("target", "")), "action", plan=action.get("plan"))

    if normalized in {"confirm agent workflow", "confirm workflow", "confirm task", "yes task"} and isinstance(PENDING_ACTION, dict) and PENDING_ACTION.get("type") == "agent_workflow":
        action = PENDING_ACTION
        PENDING_ACTION = None
        return _response(_execute_agent_workflow(action), "action", plan=action.get("plan"))

    if normalized in {"confirm auto scroll", "confirm scroll", "yes scroll"} and isinstance(PENDING_ACTION, dict) and PENDING_ACTION.get("type") == "auto_scroll":
        action = PENDING_ACTION
        PENDING_ACTION = None
        return _response(_start_auto_scroll(action.get("interval", 8.0), action.get("key_code", 0x28), action.get("startup_delay", 4.0)))

    if normalized in {"cancel action", "cancel shutdown"}:
        PENDING_ACTION = None
        PENDING_TERMINAL["command"] = None
        return _response("Action canceled.")

    if any(phrase in normalized for phrase in ["stop scrolling", "stop scroll", "stop shorts", "stop automation"]):
        return _response(_stop_auto_scroll())

    if normalized in {"stop voice", "stop speaking", "mute voice", "voice off"}:
        _save_settings({"voice_enabled": False})
        return _response("Voice muted.")

    if normalized in {"voice on", "unmute voice", "start voice"}:
        _save_settings({"voice_enabled": True})
        return _response("Voice enabled.")

    calculation_message = _handle_calculation_command(text)
    if calculation_message:
        return _response(calculation_message, "calculation")

    mode_match = re.search(r"(?:set|switch|use)\s+(simple|agent|full access|full)\s+mode", normalized)
    if mode_match:
        mode = mode_match.group(1).replace("full", "full_access").replace(" ", "_")
        if mode not in {"simple", "agent", "full_access"}:
            mode = "simple"
        _save_settings({"work_mode": mode})
        label = "Full Access" if mode == "full_access" else mode.title()
        return _response(f"{label} mode enabled. Security remains high.")

    skill_message = _skill_command_from_command(text)
    if skill_message:
        return _response(skill_message, "training", route=_route_command(text))

    if normalized in {"train model", "train brain", "train jarvis", "retrain model", "retrain brain", "train my model", "build model"}:
        return _response(_train_local_brain(), "training")

    learned_intent = _learn_intent_from_command(text)
    if learned_intent:
        return _response(learned_intent, "training")

    dataset_result = _dataset_from_command(text)
    if dataset_result:
        return _response(dataset_result, "training", route=_route_command(text))

    if normalized.startswith(("predict intent ", "detect intent ")):
        sample = re.sub(r"^(predict intent|detect intent)\s+", "", text, flags=re.IGNORECASE)
        result = predict_intent(sample)
        return _response(
            f"Intent: {result.get('intent', 'unknown')} ({result.get('confidence', 0)}) using {result.get('engine', 'local')}.",
            "training",
            intent=result,
        )

    knowledge_link = _knowledge_link_from_command(text)
    if knowledge_link:
        return _response(knowledge_link, "training")

    knowledge_text = _knowledge_text_from_command(text)
    if knowledge_text:
        return _response(knowledge_text, "training")

    knowledge_answer = _knowledge_answer_from_command(text)
    if knowledge_answer:
        return _response(knowledge_answer, "rag")

    if re.fullmatch(r"(hello|hi|hey)(\s+jarvis)?", normalized) or normalized == "jarvis":
        return _response("Hello. Jarvis is online and ready.")

    if _is_identity_question(text):
        return _response(_jarvis_identity_answer(), "answer")

    if re.search(r"\btime\b", normalized):
        return _response(f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}.")

    if re.search(r"\b(date|day)\b", normalized):
        return _response(f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}.")

    crawl_message = _crawl_command(text)
    if crawl_message:
        return _response(crawl_message, "scrape", route=_route_command(text))

    if re.fullmatch(r"(just\s+)?scroll(\s+(down|up))?", normalized):
        direction = "up" if "up" in normalized else "down"
        return _response(_scroll_once(direction))

    url_match = re.search(r"https?://\S+|(?:www\.)\S+\.\S+", text, re.IGNORECASE)
    if url_match and any(word in normalized for word in ["read", "summarize", "summary", "link"]):
        return _response(_read_link(url_match.group(0)))

    if any(phrase in normalized for phrase in ["scroll shorts", "scroll the shorts", "auto scroll", "start scrolling", "scroll youtube shorts", "keep scrolling"]):
        if "youtube" in normalized or "short" in normalized:
            webbrowser.open("https://www.youtube.com/shorts")
        return _confirm_auto_scroll(text)

    terminal_match = re.search(r"^(?:terminal|run command|run terminal|shell|cmd)\s+(.+)$", text, re.IGNORECASE)
    if terminal_match:
        return _confirm_terminal(terminal_match.group(1).strip())

    if _is_open_command(text):
        target = re.sub(r"^(open|launch|start|run)\s+", "", text, flags=re.IGNORECASE).strip()
        return _confirm_open_target(target, text)

    if normalized in APP_ALIASES:
        return _confirm_open_target(text, text)

    if normalized.startswith("search ") or normalized.startswith("google "):
        query = re.sub(r"^(search|google)\s+", "", text, flags=re.IGNORECASE).strip()
        return _response(_search_web(query))

    if re.search(r"\b(news|briefing)\b", normalized) or re.search(
        r"\b(latest|today|current)\b.*\b(ai|business|sports|technology|tech|india|world|science|health|education)\b",
        normalized,
    ):
        briefing = _daily_briefing(text)
        return _response(briefing["message"], "briefing", briefing=briefing, route=_route_command(text))

    share_request = None if _is_email_command(text) else _parse_share_request(text)
    if share_request:
        if not share_request["message"] or not share_request["target"]:
            return _response("Tell me what to share and where.")
        return _confirm_share(share_request["target"], share_request["message"], share_request.get("number", ""))

    if re.search(r"\bplay\b", normalized) and "youtube" in normalized:
        song = _extract_after(text, ["play", "on youtube", "youtube"])
        if not song:
            return _response("Tell me what to play on YouTube.")
        kit = _get_pywhatkit()
        if kit is not None:
            try:
                kit.playonyt(song)
                return _response(f"Playing {song} on YouTube.")
            except Exception:
                pass
        return _response(_search_web(song + " youtube"))

    if "wikipedia" in normalized:
        topic = _extract_after(text, ["search wikipedia", "wikipedia", "search", "about"])
        topic = re.sub(r"\b(and\s+)?(read|open|show|for me|to me|it)\b", " ", topic, flags=re.IGNORECASE)
        topic = _squash(topic)
        if not topic:
            return _response("Tell me the Wikipedia topic.")
        if any(word in normalized for word in ["open", "show", "go"]):
            webbrowser.open("https://en.wikipedia.org/wiki/" + urllib.parse.quote(topic.replace(" ", "_")))
        return _response(_wikipedia_summary(topic))

    if re.search(r"\bjoke\b", normalized):
        return _response(random.choice(JOKES))

    if _is_email_command(text):
        payload = _parse_email_request(text)
        if not payload["to"]:
            if re.search(r"\b(write|draft)\s+(an\s+)?email\b", text, re.IGNORECASE):
                topic = _email_topic_from_prompt(text, payload)
                return _response(_draft_email_body(topic or text, include_subject=True), "draft")
            return _response("Tell me who the email should go to.")
        if not payload["body"]:
            if re.search(r"\b(write|draft)\s+(an\s+)?email\b", text, re.IGNORECASE):
                topic = _email_topic_from_prompt(text, payload)
                return _response(_draft_email_body(topic or text, include_subject=True), "draft")
            return _response("Tell me the email body.")
        return _confirm_email(payload)

    if normalized.startswith(("write note ", "take note ", "remember ")):
        content = re.sub(r"^(write note|take note|remember)\s+", "", text, flags=re.IGNORECASE)
        return _response(_write_note(content))

    if normalized in {"read notes", "read note", "show notes", "show my notes"}:
        return _response(_read_notes())

    if normalized.startswith("write file "):
        return _response(_write_file(text))

    if normalized.startswith("read file "):
        return _response(_read_file(text))

    if _is_code_request(text):
        return _response(_code_from_prompt(text), "code", route=_route_command(text))

    agent_confirmation = _confirm_agent_workflow(text)
    if agent_confirmation:
        return agent_confirmation

    general_answer = _answer_general_question(text)
    if general_answer:
        return _response(general_answer, "answer", route=_route_command(text))

    if any(phrase in normalized for phrase in ["shutdown", "power off", "turn off pc", "turn off computer"]):
        PENDING_ACTION = "shutdown"
        return _response(
            "This will shut down the PC in 5 seconds.",
            "confirm_action",
            action="shutdown",
        )

    if normalized in {"exit", "close jarvis", "close app"}:
        return _response("Closing Jarvis.", close=True)

    reply = _local_ai_reply(text)
    if corrections:
        return _response(reply, corrected=text, corrections=corrections)
    return _response(reply)


def _origin_allowed(origin: str | None) -> bool:
    if not origin or origin == "null":
        return True

    parsed = urllib.parse.urlparse(origin)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def _verify_google_id_token(credential: str) -> tuple[dict | None, str]:
    client_id = _google_client_id()
    if not client_id:
        return None, "GOOGLE_CLIENT_ID is not configured."
    if not credential:
        return None, "Missing Google credential."

    query = urllib.parse.urlencode({"id_token": credential})
    try:
        request = urllib.request.Request(f"https://oauth2.googleapis.com/tokeninfo?{query}")
        with urllib.request.urlopen(request, timeout=8) as response:
            profile = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None, "Google credential could not be verified."

    if profile.get("aud") != client_id:
        return None, "Google credential does not match this Jarvis app."
    if str(profile.get("email_verified", "")).lower() not in {"true", "1"}:
        return None, "Google email is not verified."

    return {
        "name": profile.get("name") or profile.get("email") or "Jarvis User",
        "email": profile.get("email", ""),
        "picture": profile.get("picture", ""),
        "provider": "google",
    }, ""


def _get_pywhatkit():
    global pywhatkit, PYWHATKIT_UNAVAILABLE

    if PYWHATKIT_UNAVAILABLE:
        return None
    if pywhatkit is not None:
        return pywhatkit

    try:
        pywhatkit = __import__("pywhatkit")
        return pywhatkit
    except Exception:
        PYWHATKIT_UNAVAILABLE = True
        return None


class JarvisBridgeHandler(BaseHTTPRequestHandler):
    server_version = "JarvisLocalCore/1.0"

    def log_message(self, format, *args):  # noqa: A002
        return

    def _send_json(self, status: int, payload: dict) -> None:
        origin = self.headers.get("Origin")
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Vary", "Origin")
        if _origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin or "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Jarvis-Client")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_static(self, request_path: str) -> None:
        origin = self.headers.get("Origin")
        parsed_path = urllib.parse.urlparse(request_path).path

        if parsed_path == "/eel.js":
            encoded = b"window.eel = window.eel || {};"
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Vary", "Origin")
            if _origin_allowed(origin):
                self.send_header("Access-Control-Allow-Origin", origin or "*")
            self.end_headers()
            self.wfile.write(encoded)
            return

        relative = urllib.parse.unquote(parsed_path.lstrip("/") or "index.html")
        root = (BASE_DIR / "www").resolve()
        target = (root / relative).resolve()

        try:
            target.relative_to(root)
        except ValueError:
            self._send_json(403, {"ok": False, "message": "Static path blocked."})
            return

        if not target.is_file():
            self._send_json(404, {"ok": False, "message": "Static file not found."})
            return

        encoded = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Vary", "Origin")
        if _origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin or "*")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        if _origin_allowed(self.headers.get("Origin")):
            self._send_json(200, {"ok": True})
            return
        self._send_json(403, {"ok": False, "message": "Origin blocked."})

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path

        if path.rstrip("/") == "/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "name": "Jarvis Local Core",
                    "security": "high",
                    "desktop": True,
                    "static": True,
                    "search_stack": _search_stack_status(),
                },
            )
            return
        if path.rstrip("/") == "/settings":
            if not _origin_allowed(self.headers.get("Origin")) or self.headers.get("X-Jarvis-Client") != "command-center":
                self._send_json(403, {"ok": False, "message": "Client blocked."})
                return
            self._send_json(200, {"ok": True, "settings": _public_settings()})
            return
        if path.rstrip("/") == "/api/config":
            supabase = _supabase_config()
            self._send_json(
                200,
                {
                    "mode": "jarvis-local-core",
                    "google_client_id": _google_client_id(),
                    "supabase_url": supabase["url"],
                    "supabase_anon_key": supabase["anon_key"],
                    "desktop_connector": "connected",
                },
            )
            return
        if path == "/" or path == "/eel.js" or (BASE_DIR / "www" / path.lstrip("/")).resolve().is_relative_to((BASE_DIR / "www").resolve()):
            self._send_static(self.path)
            return
        self._send_json(404, {"ok": False, "message": "Not found."})

    def do_POST(self) -> None:
        route = self.path.rstrip("/")
        if route not in {"/command", "/settings", "/api/auth"}:
            self._send_json(404, {"ok": False, "message": "Not found."})
            return

        if not _origin_allowed(self.headers.get("Origin")):
            self._send_json(403, {"ok": False, "message": "Origin blocked."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(min(length, 8192)).decode("utf-8")
            data = json.loads(body or "{}")

            if route == "/api/auth":
                user, error = _verify_google_id_token(_squash(data.get("credential", "")))
                if error:
                    self._send_json(401 if _google_client_id() else 503, {"ok": False, "error": error})
                    return
                self._send_json(200, {"ok": True, "user": user})
                return

            if self.headers.get("X-Jarvis-Client") != "command-center":
                self._send_json(403, {"ok": False, "message": "Client blocked."})
                return

            if route == "/settings":
                updates = data.get("settings", data)
                if not isinstance(updates, dict):
                    raise ValueError("Invalid settings payload")
                saved = _save_settings(updates)
                self._send_json(200, {"ok": True, "settings": _public_settings(saved)})
                return

            command = data.get("command", "")
            result = process_command(command)
            parsed = json.loads(result) if isinstance(result, str) else result
            if not isinstance(parsed, dict):
                parsed = {"type": "response", "message": str(parsed)}
            self._send_json(200, parsed)
        except Exception as error:
            self._send_json(500, {"type": "error", "message": f"Command failed: {error}"})


class JarvisThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def start_bridge_server(block: bool = False) -> None:
    try:
        server = JarvisThreadingHTTPServer((CORE_HOST, CORE_PORT), JarvisBridgeHandler)
    except OSError:
        return

    if block:
        print(f"Jarvis local core running at http://{CORE_HOST}:{CORE_PORT}")
        server.serve_forever()
        return

    threading.Thread(target=server.serve_forever, daemon=True).start()


if __name__ == "__main__":
    start_bridge_server(block="--bridge-only" in sys.argv)
    if "--bridge-only" in sys.argv:
        raise SystemExit(0)
    eel.start("index.html", mode="edge", size=(1360, 860))
