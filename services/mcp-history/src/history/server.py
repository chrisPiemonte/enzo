"""MCP server for the service history data product: past faults, actions and parts per instrument."""

# pylint: disable=duplicate-code  # MOCK: same lookup as telemetry until the implementations are designed

import os
from pathlib import Path
from typing import Any

import yaml
from core.auth import DENIED, authorize
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

PORT = 9002
SECRET = os.environ["IDENTITY_SECRET"]
DATA = yaml.safe_load((Path(__file__).parents[2] / "data.yaml").read_text())

server = MCPServer("history", version="1")


@server.tool(description="Past faults, actions taken and parts used on an instrument.")
def get_service_history(serial: str, ctx: Context) -> dict[str, Any]:
    """Return an instrument's service history.

    Args:
        serial: Instrument serial number, e.g. SN-1001.
        ctx: The MCP request; its headers carry the caller's tokens.

    Returns:
        Past service events, with record_ids and dataset_version.

    Raises:
        ToolError: Access denied: the agent lacks the scope or the user is not entitled to the account.
    """
    # MOCK: returns the canned record.
    record = DATA["instruments"].get(serial)
    if record is None:
        return {"error": f"unknown instrument {serial}"}
    try:
        authorize(ctx.headers, SECRET, "history:read", record["account"])
    except PermissionError as error:  # a ToolError keeps its message; the gateway reports it as DENY
        raise ToolError(f"{DENIED}: {error}") from error
    return {"serial": serial, **record, "dataset_version": DATA["dataset_version"]}


def run() -> None:
    """Serve the tools over MCP streamable HTTP."""
    server.run(transport="streamable-http", host="0.0.0.0", port=PORT)
