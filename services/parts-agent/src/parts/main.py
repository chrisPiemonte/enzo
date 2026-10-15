"""Entrypoint: serve the agent card and the A2A JSON-RPC endpoint."""

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.utils import DEFAULT_RPC_URL
from starlette.applications import Starlette

from parts.card import CARD, PORT
from parts.executor import PartsExecutor


def run() -> None:
    """Start the agent's HTTP server."""
    handler = DefaultRequestHandler(agent_executor=PartsExecutor(), task_store=InMemoryTaskStore(), agent_card=CARD)
    app = Starlette(routes=[*create_agent_card_routes(CARD), *create_jsonrpc_routes(handler, DEFAULT_RPC_URL)])
    uvicorn.run(app, host="0.0.0.0", port=PORT)
