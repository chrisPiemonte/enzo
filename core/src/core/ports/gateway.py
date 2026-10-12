"""Port to the gateway: the single door to models, tools and agents."""

from typing import Protocol

from core.models.agents import AgentTask, TaskReply
from core.models.chat import Completion, Message, SkillCall, SkillResult, SkillSpec
from core.models.identity import Identity


class GatewayError(RuntimeError):
    """The gateway could not be reached or failed to answer."""


class Gateway(Protocol):
    """Completes conversations, lists and calls tools, and relays answers to agents waiting for input."""

    async def complete(self, messages: list[Message], tools: list[SkillSpec], identity: Identity) -> Completion:
        """Ask the model for its next turn.

        Args:
            messages: The conversation so far.
            tools: Tools the model may call.
            identity: User and agent on whose behalf the model is called.

        Returns:
            The model's text and/or tool calls.

        Raises:
            GatewayError: If the gateway fails.
        """

    async def list_tools(self) -> list[SkillSpec]:
        """List the tools of every running service: MCP tools and agent card skills.

        Returns:
            The current tool catalogue.

        Raises:
            GatewayError: If the gateway fails.
        """

    async def call_tool(self, call: SkillCall, identity: Identity) -> SkillResult:
        """Call a tool on whichever service owns it.

        Args:
            call: The tool call requested by the model.
            identity: User and agent behind the call.

        Returns:
            The result; for an agent skill, also the task it started.

        Raises:
            GatewayError: If the gateway fails.
        """

    async def reply(self, reply: TaskReply, identity: Identity) -> AgentTask:
        """Pass the user's answer to an agent whose task is waiting for input.

        Args:
            reply: Agent, task and answer.
            identity: User answering, and the agent relaying it.

        Returns:
            The task's state after the agent's reply.

        Raises:
            GatewayError: If the gateway fails.
        """
