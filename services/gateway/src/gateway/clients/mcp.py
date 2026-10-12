"""Talk to an MCP server over streamable HTTP."""

import httpx2
from core.models.chat import SkillSpec
from core.tracing import traced
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mlflow.entities import SpanType

PATH = "/mcp"


async def list_tools(url: str) -> list[SkillSpec]:
    """List the tools an MCP server offers.

    Args:
        url: Base URL of the server.

    Returns:
        The server's tools, in the shared tool format.
    """
    async with Client(f"{url}{PATH}") as client:
        result = await client.list_tools()
    return [
        SkillSpec(name=tool.name, description=tool.description or "", input_schema=tool.input_schema)
        for tool in result.tools
    ]


@traced("mcp_call_tool", SpanType.TOOL)
async def call_tool(url: str, name: str, args: dict[str, object], headers: dict[str, str]) -> tuple[bool, str]:
    """Call one tool on an MCP server, on behalf of the caller.

    Args:
        url: Base URL of the server.
        name: Tool name.
        args: Tool arguments.
        headers: The caller's token headers; the server checks them.

    Returns:
        Whether the tool reported an error, and its text output.
    """
    transport = streamable_http_client(f"{url}{PATH}", http_client=httpx2.AsyncClient(headers=headers))
    async with Client(transport) as client:
        result = await client.call_tool(name, args)
    text = "\n".join(block.text for block in result.content if block.type == "text")
    return result.is_error, text
