"""Talk to an MCP server over streamable HTTP."""

from core.models.chat import SkillSpec
from mcp import Client

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


async def call_tool(url: str, name: str, args: dict[str, object]) -> tuple[bool, str]:
    """Call one tool on an MCP server.

    Args:
        url: Base URL of the server.
        name: Tool name.
        args: Tool arguments.

    Returns:
        Whether the tool reported an error, and its text output.
    """
    async with Client(f"{url}{PATH}") as client:
        result = await client.call_tool(name, args)
    text = "\n".join(block.text for block in result.content if block.type == "text")
    return result.is_error, text
