"""MCP server for the telemetry data product: recent readings and error codes per instrument."""

import os
from pathlib import Path
from typing import Any

import yaml
from core.auth import authorize
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

PORT = 9001
SECRET = os.environ["IDENTITY_SECRET"]
DATA = yaml.safe_load((Path(__file__).parents[2] / "data.yaml").read_text())

server = MCPServer("telemetry", version="1")


@server.tool(description="Recent readings and error codes reported by an instrument.")
def get_recent_telemetry(serial: str, ctx: Context, hours: int = 24) -> dict[str, Any]:
    """Return an instrument's recent readings and error codes.

    Args:
        serial: Instrument serial number, e.g. SN-1001.
        ctx: The MCP request; its headers carry the caller's tokens.
        hours: How many hours back to look.

    Returns:
        Readings summary and error counts, with record_ids and dataset_version.

    Raises:
        ToolError: Access denied: the agent lacks the scope or the user is not entitled to the account.
    """
    # MOCK: returns the canned record; ignores hours.
    record = DATA["instruments"].get(serial)
    if record is None:
        return {"error": f"unknown instrument {serial}"}
    try:
        authorize(ctx.headers, SECRET, "telemetry:read", record["account"])
    except PermissionError as error:  # a ToolError keeps its message; the gateway reports it as DENY
        raise ToolError(f"access denied: {error}") from error
    return {"serial": serial, **record, "dataset_version": DATA["dataset_version"]}


def run() -> None:
    """Serve the tools over MCP streamable HTTP."""
    server.run(transport="streamable-http", host="0.0.0.0", port=PORT)
