from __future__ import annotations

from .schemas import AgentPlan, RiskLevel, TaskIntent


ACTIONABLE_INTENTS = {
    TaskIntent.BROWSER,
    TaskIntent.CODE,
    TaskIntent.EMAIL,
    TaskIntent.FILE,
    TaskIntent.DEPLOY,
    TaskIntent.DESKTOP_CONNECTOR,
}


HIGH_RISK_INTENTS = {
    TaskIntent.EMAIL,
    TaskIntent.FILE,
    TaskIntent.DEPLOY,
    TaskIntent.DESKTOP_CONNECTOR,
}


def apply_security_policy(plan: AgentPlan) -> AgentPlan:
    """Approval-first policy for cloud Jarvis.

    All actions that can change state, contact another person, run code, deploy,
    or control a browser session require explicit approval. Normal answers and
    read-only search can run without approval.
    """

    if plan.intent in ACTIONABLE_INTENTS:
        plan.requires_approval = True

    if plan.intent in HIGH_RISK_INTENTS:
        plan.risk = RiskLevel.HIGH

    if plan.intent == TaskIntent.DEPLOY:
        plan.risk = RiskLevel.CRITICAL

    return plan
