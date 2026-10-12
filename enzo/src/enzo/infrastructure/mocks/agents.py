"""A canned parts agent skill, for working without the gateway."""

import uuid

from core.models.agents import AgentTask, TaskReply
from core.models.chat import SkillCall, SkillResult, SkillSpec

AGENT = "parts-agent"
ORDER_TOOL = SkillSpec(
    name="order_part_and_schedule_visit",
    description="Propose a parts order for an instrument and a technician visit window. Needs approval. "
    "Examples: Order heater assembly P-123 for SN-1001 and schedule a visit.",
    input_schema={"type": "object", "properties": {"request": {"type": "string"}}, "required": ["request"]},
)


def order(call: SkillCall) -> SkillResult:
    """Start an order task that waits for the user's approval.

    Args:
        call: The order call; its request is ignored.

    Returns:
        The result, carrying an input-required task.
    """
    message = "Order heater assembly P-123 for SN-1001, technician visit Tue 14:00–16:00. Approve?"
    task = AgentTask(agent=AGENT, task_id=uuid.uuid4().hex[:8], state="input-required", message=message)
    source = f"a2a:{AGENT}"
    return SkillResult(call_id=call.id, name=call.name, decision="ALLOW", content=message, source=source, task=task)


def reply(answer: TaskReply) -> AgentTask:
    """Complete the order on approve/yes, reject it on reject/no, ask again otherwise.

    Args:
        answer: The user's answer to the waiting task.

    Returns:
        The completed, rejected or still waiting task.
    """
    word = answer.answer.strip().lower()
    if word in {"approve", "yes", "y", "ok"}:
        message = "Order ORD-4711 placed. Technician visit booked Tue 14:00–16:00."
        return AgentTask(agent=AGENT, task_id=answer.task_id, state="completed", message=message)
    if word in {"reject", "no", "n"}:
        return AgentTask(agent=AGENT, task_id=answer.task_id, state="rejected", message="Order not placed.")
    ask = "Please answer approve or reject."
    return AgentTask(agent=AGENT, task_id=answer.task_id, state="input-required", message=ask)
