"""Find the MCP servers and A2A agents that are running, from their Docker labels."""

import json
from typing import Literal

import httpx
from core.tracing import traced
from mlflow.entities import SpanType
from pydantic import BaseModel

ServiceKind = Literal["mcp", "a2a"]


class Service(BaseModel):
    """A running service the gateway can route to."""

    name: str
    kind: ServiceKind
    url: str


class DiscoveryError(RuntimeError):
    """Docker could not be asked which services are running."""


@traced("discover_services", SpanType.RETRIEVER)
async def discover(docker_socket: str) -> list[Service]:
    """List running containers labelled enzo.kind (mcp or a2a), as services.

    Args:
        docker_socket: Path to the Docker Engine socket.

    Returns:
        One service per labelled container, addressed by its compose service name.

    Raises:
        DiscoveryError: If the Docker socket cannot be reached.
    """
    transport = httpx.AsyncHTTPTransport(uds=docker_socket)
    filters = json.dumps({"label": ["enzo.kind"]})
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://docker") as client:
            response = await client.get("/containers/json", params={"filters": filters})
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise DiscoveryError(f"cannot reach Docker at {docker_socket}: {error!r}") from error
    services = []
    for container in response.json():
        labels = container["Labels"]
        name = labels["com.docker.compose.service"]
        services.append(Service(name=name, kind=labels["enzo.kind"], url=f"http://{name}:{labels['enzo.port']}"))
    return sorted(services, key=lambda service: service.name)
