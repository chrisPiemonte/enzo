"""A2A executor: runs each task through the ordering logic, pausing for approval."""

from pathlib import Path

import yaml
from a2a.helpers.proto_helpers import new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Part
from core.auth import DENIED

from parts.access import check_approval, check_request
from parts.orders import Proposal, decide, propose

DATA = yaml.safe_load((Path(__file__).parents[2] / "data.yaml").read_text())


class PartsExecutor(AgentExecutor):
    """New task: propose an order and ask for approval. Continued task: place or drop the order."""

    def __init__(self) -> None:
        """Start with no proposals waiting."""
        self.waiting: dict[str, Proposal] = {}  # task id -> proposal awaiting approval

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle one message, for a new task or one waiting for approval.

        Args:
            context: The request, with the task and the caller's message.
            event_queue: Where task updates are published.
        """
        task = context.current_task
        if task is None and context.message is not None:  # a new task must be published before any update
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)
        task_id, text = (task.id if task else ""), context.get_user_input()
        updater = TaskUpdater(event_queue, task_id, task.context_id if task else "")
        headers = context.call_context.state.get("headers", {}) if context.call_context else {}
        proposal = self.waiting.get(task_id)

        if proposal is None:
            try:
                result = propose(text, DATA, lambda account: check_request(headers, account))
            except PermissionError as error:
                await updater.reject(_say(updater, f"{DENIED}: {error}"))
                return
            if isinstance(result, str):
                await updater.reject(_say(updater, result))
                return
            self.waiting[task_id] = result
            await updater.requires_input(_say(updater, result.question()))
            return

        match decide(text):
            case "approve":
                del self.waiting[task_id]
                try:
                    check_approval(headers, proposal.account)
                except PermissionError as error:  # fail closed: the order is dropped, not left waiting
                    await updater.reject(_say(updater, f"{DENIED}: {error}"))
                    return
                order = f"ORD-{task_id[:6].upper()}"
                done = f"Order {order} placed for {proposal.part}. Visit {proposal.visit}."
                await updater.complete(_say(updater, done))
            case "reject":
                del self.waiting[task_id]
                await updater.reject(_say(updater, "Order not placed."))
            case None:
                await updater.requires_input(_say(updater, "Please answer approve or reject."))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Drop a waiting proposal.

        Args:
            context: The request naming the task.
            event_queue: Where the cancellation is published.
        """
        self.waiting.pop(context.task_id or "", None)
        await TaskUpdater(event_queue, context.task_id or "", context.context_id or "").cancel()


def _say(updater: TaskUpdater, text: str) -> Message:
    """Wrap text as a message from this agent.

    Args:
        updater: The task's updater.
        text: The text.

    Returns:
        The A2A message.
    """
    return updater.new_agent_message([Part(text=text)])
