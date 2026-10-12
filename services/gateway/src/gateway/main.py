"""Entrypoint: serve the gateway API with uvicorn."""

import uvicorn

from gateway.settings import settings


def run() -> None:
    """Start the gateway HTTP server."""
    uvicorn.run("gateway.api:app", host=settings.host, port=settings.port)
