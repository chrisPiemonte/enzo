"""Adapter calling the gateway service over HTTP."""

from typing import Any

import httpx
from mlflow.tracing import get_tracing_context_headers_for_http_request

from core.models.agents import AgentTask, TaskReply
from core.models.chat import Completion, CompletionRequest, Message, SkillCall, SkillResult, SkillSpec
from core.models.identity import Identity
from core.ports.gateway import GatewayError

TIMEOUT_SECONDS = 120  # CPU-only Ollama in Docker can take ~30 s per turn


class HttpGateway:
    """Talks to the gateway's REST API; model calls go under an alias, the gateway picks provider and model."""

    def __init__(self, url: str, alias: str) -> None:
        """Create the adapter.

        Args:
            url: Base URL of the gateway service.
            alias: Model alias the gateway resolves, e.g. triage-default.
        """
        self.url, self.alias = url, alias

    async def complete(self, messages: list[Message], tools: list[SkillSpec], identity: Identity) -> Completion:
        """Ask the gateway for the model's next turn.

        Args:
            messages: The conversation so far.
            tools: Tools the model may call.
            identity: User and agent behind the call.

        Returns:
            The model's text and/or tool calls.
        """
        request = CompletionRequest(model=self.alias, messages=messages, tools=tools)
        return Completion.model_validate(await self._send("POST", "/v1/complete", identity, request.model_dump()))

    async def list_tools(self) -> list[SkillSpec]:
        """List the tools of every running service.

        Returns:
            The current tool catalogue.
        """
        return [SkillSpec.model_validate(tool) for tool in await self._send("GET", "/v1/tools")]

    async def call_tool(self, call: SkillCall, identity: Identity) -> SkillResult:
        """Call a tool through the gateway.

        Args:
            call: The tool call requested by the model.
            identity: User and agent behind the call.

        Returns:
            The tool's result.
        """
        return SkillResult.model_validate(await self._send("POST", "/v1/tools/call", identity, call.model_dump()))

    async def reply(self, reply: TaskReply, identity: Identity) -> AgentTask:
        """Pass the user's answer to an agent waiting for input.

        Args:
            reply: Agent, task and answer.
            identity: User answering, and the agent relaying it.

        Returns:
            The task's state after the agent's reply.
        """
        return AgentTask.model_validate(await self._send("POST", "/v1/tasks/reply", identity, reply.model_dump()))

    async def _send(self, method: str, path: str, identity: Identity | None = None, body: Any = None) -> Any:
        """Send one request to the gateway.

        Args:
            method: HTTP method.
            path: Path under the gateway URL.
            identity: Sent as headers; STUB until signed tokens replace them. The trace context is sent too.
            body: JSON body, if any.

        Returns:
            The decoded JSON response.

        Raises:
            GatewayError: If the gateway is unreachable or answers with an error.
        """
        headers = {"X-User": identity.user, "X-Agent": identity.agent} if identity else {}
        headers |= get_tracing_context_headers_for_http_request()  # the gateway continues the caller's trace
        try:
            async with httpx.AsyncClient(base_url=self.url, timeout=TIMEOUT_SECONDS) as client:
                response = await client.request(method, path, json=body, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise GatewayError(f"{error.response.status_code} {error.response.text}") from error
        except httpx.HTTPError as error:
            raise GatewayError(f"cannot reach the gateway at {self.url}: {error!r}") from error
        return response.json()
