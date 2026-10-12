"""MCP server for the service manuals data product: search the manual of an instrument model."""

from pathlib import Path
from typing import Any

import yaml
from mcp.server import MCPServer

PORT = 9003
DATA = yaml.safe_load((Path(__file__).parents[2] / "data.yaml").read_text())

server = MCPServer("manuals", version="1")


@server.tool(description="Search the service manual of an instrument model, e.g. for a fault code.")
def search_manual(model: str, query: str) -> dict[str, Any]:
    """Return the manual sections of a model that match a query.

    Args:
        model: Instrument model, e.g. GC-X100.
        query: What to look for, e.g. a fault code such as E42.

    Returns:
        Matching sections, with record_ids and dataset_version.
    """
    # MOCK: plain substring match standing in for retrieval (the RAG comes later).
    sections = DATA["models"].get(model)
    if sections is None:
        return {"error": f"no manual for model {model}"}
    hits = [s for s in sections if query.lower() in f"{s['code']} {s['text']}".lower()]
    record_ids = [f"man-{model.lower()}-{s['section']}" for s in hits]
    return {"model": model, "sections": hits, "record_ids": record_ids, "dataset_version": DATA["dataset_version"]}


def run() -> None:
    """Serve the tools over MCP streamable HTTP."""
    server.run(transport="streamable-http", host="0.0.0.0", port=PORT)
