"""Bookkeeping for one answer: the steps shown to the user and their audit events."""

from collections.abc import Callable

from core.models.audit import AuditEvent
from core.models.identity import Decision, Identity
from core.models.reply import ToolCall

from core.ports.audit_log import AuditLog


class Recorder:
    """Collects the steps of one trace and writes an audit event for each."""

    def __init__(
        self, audit: AuditLog, identity: Identity, trace_id: str, on_step: Callable[[ToolCall], None] | None = None
    ) -> None:
        """Start recording a trace.

        Args:
            audit: Where audit events go.
            identity: User and agent behind every step.
            trace_id: The trace being recorded.
            on_step: Called with each step as it happens, e.g. to show progress live.
        """
        self.audit, self.identity, self.trace_id, self.on_step = audit, identity, trace_id, on_step
        self.steps: list[ToolCall] = []
        self.shown = 0  # how many steps have already been handed out

    async def record(self, target: str, action: str, decision: Decision = "ALLOW", model: str | None = None) -> None:
        """Record one step.

        Args:
            target: What was called, e.g. skill or a2a:parts-agent.
            action: What was done, e.g. the tool name.
            decision: Outcome of the access check.
            model: Model that requested the step, if any.
        """
        self.steps.append(ToolCall(service=target, action=action, decision=decision))
        if self.on_step:
            self.on_step(self.steps[-1])
        event = AuditEvent(
            trace_id=self.trace_id, user=self.identity.user, agent=self.identity.agent,
            action=action, target=target, decision=decision, model=model,
        )
        await self.audit.record(event)

    def new_steps(self) -> list[ToolCall]:
        """Return the steps recorded since the last call, so each reply shows only its own steps.

        Returns:
            The new steps.
        """
        new, self.shown = self.steps[self.shown :], len(self.steps)
        return new
