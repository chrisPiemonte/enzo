"""MCP server for the telemetry data product: recent readings and error codes per instrument."""

from pathlib import Path
from typing import Any

import yaml
from mcp.server import MCPServer

PORT = 9001
DATA = yaml.safe_load((Path(__file__).parents[2] / "data.yaml").read_text())

server = MCPServer("telemetry", version="1")


@server.tool(description="Recent readings and error codes reported by an instrument.")
def get_recent_telemetry(serial: str, hours: int = 24) -> dict[str, Any]:
    """Return an instrument's recent readings and error codes.

    Args:
        serial: Instrument serial number, e.g. SN-1001.
        hours: How many hours back to look.

    Returns:
        Readings summary and error counts, with record_ids and dataset_version.
    """
    # MOCK: returns the canned record; ignores hours and checks no entitlement.
    record = DATA["instruments"].get(serial)
    if record is None:
        return {"error": f"unknown instrument {serial}"}
    return {"serial": serial, **record, "dataset_version": DATA["dataset_version"]}


def run() -> None:
    """Serve the tools over MCP streamable HTTP."""
    server.run(transport="streamable-http", host="0.0.0.0", port=PORT)
