from __future__ import annotations

from .planner import JarvisPlanner
from .providers import LLMMessage, get_provider
from .schemas import AgentPlan, AgentResult, TaskIntent
from .tools.browser import CloudBrowserTool


class JarvisOrchestrator:
    def __init__(self) -> None:
        self.planner = JarvisPlanner()
        self.provider = get_provider()
        self.browser = CloudBrowserTool()

    async def plan(self, prompt: str) -> AgentPlan:
        return self.planner.plan(prompt)

    async def run(self, prompt: str, plan: AgentPlan | None = None) -> AgentResult:
        plan = plan or self.planner.plan(prompt)

        if plan.intent == TaskIntent.SEARCH:
            results = await self.browser.search(prompt)
            answer = self._format_search_answer(prompt, results)
            return AgentResult(answer=answer, sources=[{"title": r["title"], "url": r["url"]} for r in results])

        if plan.intent == TaskIntent.READ_LINK and plan.actions and plan.actions[0].target:
            page = await self.browser.read_url(plan.actions[0].target)
            summary = await self._summarize_text(prompt, page["text"])
            return AgentResult(
                answer=f"{page['title']}\n\n{summary}",
                sources=[{"title": page["title"], "url": page["url"]}],
                technical_details={"extractor": "playwright_or_http_fallback"},
            )

        if plan.intent == TaskIntent.BROWSER:
            return AgentResult(
                answer=(
                    "I prepared a cloud browser session for this task. "
                    "The worker can open Chromium, interact with the page, and stream progress after approval."
                ),
                technical_details={"actions": [action.model_dump() for action in plan.actions]},
            )

        if plan.intent == TaskIntent.EMAIL:
            draft = await self._generate_email(prompt)
            return AgentResult(answer=draft, technical_details={"approval_required": True})

        if plan.intent == TaskIntent.DESKTOP_CONNECTOR:
            return AgentResult(
                answer=(
                    "Direct laptop control is now optional hybrid mode. "
                    "Cloud Jarvis can plan the action, but opening local apps such as VS Code requires a user-installed connector."
                ),
                technical_details={"connector": "optional"},
            )

        answer = await self.provider.generate(
            [
                LLMMessage(
                    role="system",
                    content=(
                        "You are Jarvis, a direct cloud AI agent. Answer with the direct answer first, "
                        "then concise explanation, then technical details only if useful."
                    ),
                ),
                LLMMessage(role="user", content=prompt),
            ]
        )
        return AgentResult(answer=answer)

    async def _summarize_text(self, prompt: str, text: str) -> str:
        return await self.provider.generate(
            [
                LLMMessage(role="system", content="Summarize extracted web text for a user. Be direct and remove boilerplate."),
                LLMMessage(role="user", content=f"User asked: {prompt}\n\nSource text:\n{text[:6000]}"),
            ]
        )

    async def _generate_email(self, prompt: str) -> str:
        return await self.provider.generate(
            [
                LLMMessage(
                    role="system",
                    content=(
                        "Draft complete email messages. Include subject and body. "
                        "Do not claim the email was sent. Ask for approval before sending."
                    ),
                ),
                LLMMessage(role="user", content=prompt),
            ]
        )

    @staticmethod
    def _format_search_answer(query: str, results: list[dict[str, str]]) -> str:
        if not results:
            return "I could not find reliable search results for that query right now."
        lines = [f"Search results for: {query}", ""]
        for index, result in enumerate(results, start=1):
            lines.append(f"{index}. {result['title']}")
            if result.get("snippet"):
                lines.append(f"   {result['snippet']}")
            if result.get("url"):
                lines.append(f"   Source: {result['url']}")
            lines.append("")
        return "\n".join(lines).strip()
