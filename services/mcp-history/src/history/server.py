"""MCP server for the service history data product: past faults, actions and parts per instrument."""

# pylint: disable=duplicate-code  # MOCK: same lookup as telemetry until the implementations are designed

from pathlib import Path
from typing import Any

import yaml
from mcp.server import MCPServer

PORT = 9002
DATA = yaml.safe_load((Path(__file__).parents[2] / "data.yaml").read_text())

server = MCPServer("history", version="1")


@server.tool(description="Past faults, actions taken and parts used on an instrument.")
def get_service_history(serial: str) -> dict[str, Any]:
    """Return an instrument's service history.

    Args:
        serial: Instrument serial number, e.g. SN-1001.

    Returns:
        Past service events, with record_ids and dataset_version.
    """
    # MOCK: returns the canned record and checks no entitlement.
    record = DATA["instruments"].get(serial)
    if record is None:
        return {"error": f"unknown instrument {serial}"}
    return {"serial": serial, **record, "dataset_version": DATA["dataset_version"]}


def run() -> None:
    """Serve the tools over MCP streamable HTTP."""
    server.run(transport="streamable-http", host="0.0.0.0", port=PORT)
