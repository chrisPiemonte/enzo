"""What the agent and the model gateway exchange: messages, tools and completions."""

from typing import Any, Literal

from pydantic import BaseModel

from core.models.agents import AgentTask
from core.models.identity import Decision

Role = Literal["system", "user", "assistant", "tool"]


class SkillSpec(BaseModel):
    """A skill offered to the model as a tool."""

    name: str
    description: str
    input_schema: dict[str, Any]


class SkillCall(BaseModel):
    """A skill call requested by the model."""

    id: str
    name: str
    args: dict[str, Any]


class SkillResult(BaseModel):
    """The outcome of a tool call, sent back to the model."""

    call_id: str
    name: str
    decision: Decision
    content: str
    source: str = ""  # who answered, e.g. mcp:mcp-telemetry or a2a:parts-agent
    task: AgentTask | None = None  # set when the tool is an agent skill; input-required means a hand-off


class Message(BaseModel):
    """One turn of the conversation."""

    role: Role
    content: str
    skill_calls: list[SkillCall] = []
    call_id: str | None = None


class CompletionRequest(BaseModel):
    """A request to the model gateway."""

    model: str
    messages: list[Message]
    tools: list[SkillSpec] = []
    provider: str | None = None
    provider_model: str | None = None


class Completion(BaseModel):
    """The model gateway's answer."""

    model: str
    provider: str
    text: str | None
    skill_calls: list[SkillCall] = []
