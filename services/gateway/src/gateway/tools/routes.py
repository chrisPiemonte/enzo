"""HTTP routes for tools: list the catalogue, call a tool, reply to a waiting task."""

from typing import Annotated

from core.auth import DENIED
from core.models.agents import AgentTask, TaskReply
from core.models.chat import SkillCall, SkillResult, SkillSpec
from core.models.identity import Decision
from fastapi import APIRouter, Depends, HTTPException

from gateway.auth import caller_tokens
from gateway.clients import a2a, mcp
from gateway.registry.discovery import DiscoveryError, Service, discover
from gateway.settings import settings
from gateway.tools.catalog import Entry, build_catalog

router = APIRouter(prefix="/v1", dependencies=[Depends(caller_tokens)])
Tokens = Annotated[dict[str, str], Depends(caller_tokens)]


@router.get("/tools")
async def tools() -> list[SkillSpec]:
    """List every tool currently offered by the running services.

    Returns:
        The tool catalogue, rebuilt from the services running right now.
    """
    return [entry.spec for entry in (await _catalog()).values()]


@router.post("/tools/call")
async def call(request: SkillCall, tokens: Tokens) -> SkillResult:
    """Call a tool on the service that owns it.

    Args:
        request: Tool name, call id and arguments.
        tokens: The caller's token headers, forwarded to the service.

    Returns:
        The tool's output; for an agent skill, also the task it started.

    Raises:
        HTTPException: 404 if no running service offers the tool.
    """
    entry = (await _catalog()).get(request.name)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"no running service offers {request.name!r}")
    source = f"{entry.service.kind}:{entry.service.name}"
    if entry.service.kind == "a2a":
        task = await a2a.send(entry.service.url, entry.service.name, str(request.args.get("request", "")), tokens)
        decision: Decision = "DENY" if task.message.startswith(DENIED) else "ALLOW"
        return SkillResult(
            call_id=request.id, name=request.name, decision=decision, content=task.message, source=source, task=task
        )
    failed, text = await mcp.call_tool(entry.service.url, request.name, request.args, tokens)
    mcp_decision: Decision = "DENY" if failed else "ALLOW"
    return SkillResult(call_id=request.id, name=request.name, decision=mcp_decision, content=text, source=source)


@router.post("/tasks/reply")
async def reply(request: TaskReply, tokens: Tokens) -> AgentTask:
    """Pass the user's answer to the agent whose task is waiting for input.

    Args:
        request: Agent, task and the user's answer.
        tokens: The caller's token headers, forwarded to the agent.

    Returns:
        The task's state after the agent's reply.

    Raises:
        HTTPException: 404 if the agent is not running.
    """
    service = next((s for s in await _services() if s.name == request.agent and s.kind == "a2a"), None)
    if service is None:
        raise HTTPException(status_code=404, detail=f"agent {request.agent!r} is not running")
    return await a2a.send(service.url, service.name, request.answer, tokens, request.task_id)


async def _catalog() -> dict[str, Entry]:
    """Build the catalogue from the services running now.

    Returns:
        Tool name -> tool and owning service.
    """
    return await build_catalog(await _services())


async def _services() -> list[Service]:
    """Discover the running services.

    Returns:
        The running services.

    Raises:
        HTTPException: 503 if Docker cannot be reached.
    """
    try:
        return await discover(settings.docker_socket)
    except DiscoveryError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
