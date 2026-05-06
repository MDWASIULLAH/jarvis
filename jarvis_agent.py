import re


ACTION_WORDS = (
    "open",
    "launch",
    "start",
    "run",
    "create",
    "make",
    "build",
    "send",
    "message",
    "email",
    "deploy",
    "install",
    "edit",
    "write file",
    "terminal",
    "shutdown",
    "scroll",
)


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_wake_word(command: str) -> str:
    text = squash(command)
    text = re.sub(r"^(hey|hi|hello|ok|okay)\s+jarvis[,\s:;-]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^jarvis[,\s:;-]+", "", text, flags=re.IGNORECASE)
    return squash(text)


def clean_open_target(target: str) -> str:
    value = squash(target).strip(" .,!?:;")
    value = re.sub(r"^(my|the|a|an)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+(app|application|program|software)$", "", value, flags=re.IGNORECASE)
    replacements = {
        "vs code": "visual studio code",
        "vscode": "visual studio code",
        "visual code": "visual studio code",
        "youtube short": "youtube shorts",
    }
    return replacements.get(value.lower(), value)


def _intent_for(text: str) -> str:
    normalized = text.lower()
    if re.match(r"^(open|launch|start)\s+", normalized):
        return "open_app_or_site"
    if re.search(r"\b(send|draft|write)\s+(an\s+)?email\b", normalized):
        return "email"
    if re.search(r"\b(message|whatsapp|share)\b", normalized):
        return "message_or_share"
    if re.search(r"\b(write|generate|create|build|fix|debug)\b.*\b(code|project|react|next|python|node|app|website)\b", normalized):
        return "coding"
    if re.search(r"\b(deploy|vercel|github|repo|commit|push)\b", normalized):
        return "deployment"
    if re.search(r"\b(terminal|cmd|shell|run command|install)\b", normalized):
        return "terminal"
    if re.search(r"\b(pdf|powerpoint|ppt|presentation|spreadsheet|excel)\b", normalized):
        return "document"
    if re.search(r"\b(search|latest|news|briefing|read link|summarize link)\b", normalized):
        return "research"
    if re.search(r"\b(scroll|shutdown|restart|delete|remove)\b", normalized):
        return "system_action"
    return "answer"


def plan_task(command: str) -> dict:
    cleaned = strip_wake_word(command)
    normalized = cleaned.lower()
    intent = _intent_for(cleaned)
    actionable = intent != "answer" or any(word in normalized for word in ACTION_WORDS)
    risk = "low"
    if intent in {"email", "message_or_share", "deployment", "terminal", "system_action"}:
        risk = "high"
    elif intent in {"open_app_or_site", "coding", "document"}:
        risk = "medium"

    target = ""
    if intent == "open_app_or_site":
        target = clean_open_target(re.sub(r"^(open|launch|start)\s+", "", cleaned, flags=re.IGNORECASE))

    steps = ["Understand the request", "Choose the safest tool path"]
    if actionable:
        steps.append("Ask for approval in the Jarvis UI")
        if intent == "open_app_or_site":
            steps.append(f"Open {target or 'the requested target'} through the Local Core connector")
        elif intent == "coding":
            steps.append("Generate or modify code using local coding skills and model fallback")
        elif intent == "research":
            steps.append("Search or retrieve sources with the free local search stack")
        elif intent in {"email", "message_or_share"}:
            steps.append("Prepare the draft and send/open only after approval")
        elif intent == "deployment":
            steps.append("Run git/deploy commands only after approval")
        else:
            steps.append("Execute through the Local Core connector")
    else:
        steps.append("Answer directly with useful context")

    return {
        "original": squash(command),
        "command": cleaned,
        "intent": intent,
        "actionable": actionable,
        "approval_required": actionable,
        "risk": risk,
        "target": target,
        "summary": f"{intent.replace('_', ' ').title()}: {cleaned}",
        "steps": steps,
        "execution": "local_core_required" if actionable and intent not in {"research", "answer"} else "web_or_local",
    }
