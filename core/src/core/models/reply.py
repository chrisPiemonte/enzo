"""The agent's answer to one question, and the steps behind it."""

from pydantic import BaseModel

from core.models.agents import AgentTask
from core.models.identity import Decision


class ToolCall(BaseModel):
    """One step the agent took: which service, and whether it was allowed."""

    service: str
    action: str
    decision: Decision


class AgentReply(BaseModel):
    """The agent's answer to one question, with the steps that produced it."""

    trace_id: str
    model: str
    steps: list[ToolCall]
    answer: str
    pending: AgentTask | None = None  # a remote agent took over the conversation and is waiting for the user
