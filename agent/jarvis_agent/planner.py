from __future__ import annotations

import re
from urllib.parse import urlparse

from .policies import apply_security_policy
from .schemas import AgentPlan, PlanAction, RiskLevel, TaskIntent


URL_PATTERN = re.compile(r"https?://[^\s)>\"]+", re.IGNORECASE)


class JarvisPlanner:
    """Small deterministic planner that prepares tasks before the LLM runs."""

    def plan(self, prompt: str) -> AgentPlan:
        text = " ".join(prompt.strip().split())
        lowered = text.lower()

        if not text:
            return AgentPlan(
                intent=TaskIntent.ANSWER,
                summary="Ask the user for a task.",
                steps=["Wait for a clear instruction."],
            )

        url = self._first_url(text)
        if self._looks_like_email(lowered):
            plan = AgentPlan(
                intent=TaskIntent.EMAIL,
                summary="Draft or prepare an email with approval before sending.",
                risk=RiskLevel.HIGH,
                steps=[
                    "Identify recipient, subject, and message purpose.",
                    "Draft a complete email.",
                    "Show approval card before sending.",
                    "Send only after explicit approval.",
                ],
                actions=[PlanAction(type="email.prepare", label="Prepare email draft")],
            )
        elif self._looks_like_deploy(lowered):
            plan = AgentPlan(
                intent=TaskIntent.DEPLOY,
                summary="Prepare a deployment workflow with approval.",
                risk=RiskLevel.CRITICAL,
                steps=[
                    "Inspect project type and deployment target.",
                    "Build or validate the app.",
                    "Prepare deployment command.",
                    "Run deployment only after approval.",
                ],
                actions=[PlanAction(type="deploy.prepare", label="Prepare deployment")],
            )
        elif self._looks_like_code(lowered):
            plan = AgentPlan(
                intent=TaskIntent.CODE,
                summary="Generate or modify production-ready code.",
                risk=RiskLevel.MEDIUM,
                steps=[
                    "Infer the target language and framework.",
                    "Generate complete runnable code.",
                    "Explain setup and usage.",
                    "Offer follow-up fixes when errors appear.",
                ],
                actions=[PlanAction(type="code.generate", label="Generate code")],
            )
        elif url and self._looks_like_read(lowered):
            plan = AgentPlan(
                intent=TaskIntent.READ_LINK,
                summary=f"Read and summarize {urlparse(url).netloc}.",
                steps=[
                    "Fetch the page through the cloud extraction stack.",
                    "Clean boilerplate and navigation text.",
                    "Summarize direct answer first.",
                ],
                actions=[PlanAction(type="browser.read", label="Read link", target=url)],
            )
        elif self._looks_like_search(lowered):
            plan = AgentPlan(
                intent=TaskIntent.SEARCH,
                summary="Search the web and summarize results.",
                steps=[
                    "Search with the configured open-source provider.",
                    "Open promising sources when needed.",
                    "Summarize the answer with source links.",
                ],
                actions=[PlanAction(type="search.web", label="Search web", payload={"query": text})],
            )
        elif self._looks_like_browser(lowered):
            target = self._browser_target(text)
            plan = AgentPlan(
                intent=TaskIntent.BROWSER,
                summary=f"Run a cloud browser session for {target}.",
                risk=RiskLevel.MEDIUM,
                steps=[
                    "Create an isolated Chromium browser session.",
                    "Navigate or interact according to the request.",
                    "Stream progress back to the UI.",
                    "Stop when the goal is complete or approval is revoked.",
                ],
                actions=[PlanAction(type="browser.automate", label="Automate browser", target=target)],
            )
        elif self._looks_like_desktop(lowered):
            plan = AgentPlan(
                intent=TaskIntent.DESKTOP_CONNECTOR,
                summary="Use the optional hybrid desktop connector.",
                risk=RiskLevel.HIGH,
                steps=[
                    "Explain that direct laptop control requires the optional connector.",
                    "Prepare a connector action request.",
                    "Execute only when the user approves on the web UI.",
                ],
                actions=[PlanAction(type="desktop.request", label="Request desktop connector")],
            )
        else:
            plan = AgentPlan(
                intent=TaskIntent.ANSWER,
                summary="Answer the user directly.",
                steps=[
                    "Understand the question.",
                    "Retrieve context if needed.",
                    "Answer clearly with direct answer first.",
                ],
                actions=[PlanAction(type="answer.generate", label="Generate answer")],
            )

        return apply_security_policy(plan)

    @staticmethod
    def _first_url(text: str) -> str | None:
        match = URL_PATTERN.search(text)
        return match.group(0) if match else None

    @staticmethod
    def _looks_like_email(text: str) -> bool:
        return any(word in text for word in ("send email", "draft email", "mail to", "email to"))

    @staticmethod
    def _looks_like_deploy(text: str) -> bool:
        return any(word in text for word in ("deploy", "vercel", "production release", "publish app"))

    @staticmethod
    def _looks_like_code(text: str) -> bool:
        markers = ("write code", "create react", "next.js", "python", "javascript", "typescript", "fix bug", "codebase")
        return any(marker in text for marker in markers)

    @staticmethod
    def _looks_like_read(text: str) -> bool:
        return any(word in text for word in ("read", "summarize", "analyze", "explain this link"))

    @staticmethod
    def _looks_like_search(text: str) -> bool:
        return text.startswith("search ") or any(word in text for word in ("latest", "news", "business news", "sports news", "ai news"))

    @staticmethod
    def _looks_like_browser(text: str) -> bool:
        return any(word in text for word in ("open youtube", "open website", "browse", "scroll", "click", "browser"))

    @staticmethod
    def _looks_like_desktop(text: str) -> bool:
        return any(word in text for word in ("open vs code", "open vscode", "open calculator", "open notepad", "shutdown", "terminal"))

    @staticmethod
    def _browser_target(text: str) -> str:
        url = URL_PATTERN.search(text)
        if url:
            return url.group(0)
        return text
