"""One tool catalogue across every discovered service: MCP tools and A2A agent card skills."""

import logging

from core.models.chat import SkillSpec
from core.tracing import traced
from mlflow.entities import SpanType
from pydantic import BaseModel

from gateway.clients import a2a, mcp
from gateway.registry.discovery import Service

log = logging.getLogger(__name__)

REQUEST_SCHEMA = {
    "type": "object",
    "properties": {"request": {"type": "string", "description": "What should be done, in plain words."}},
    "required": ["request"],
}


class Entry(BaseModel):
    """A tool in the catalogue and the service that owns it."""

    spec: SkillSpec
    service: Service


@traced("build_catalog", SpanType.CHAIN)
async def build_catalog(services: list[Service]) -> dict[str, Entry]:
    """Collect the tools of every service; a name already taken is refused, an unreachable service skipped.

    Args:
        services: The discovered services.

    Returns:
        Tool name -> tool and owning service.
    """
    catalog: dict[str, Entry] = {}
    for service in services:
        try:
            specs = await (mcp.list_tools(service.url) if service.kind == "mcp" else _card_tools(service.url))
        except Exception as error:  # pylint: disable=broad-exception-caught  # one bad service must not hide the rest
            log.warning("skipping %s: %r", service.name, error)
            continue
        for spec in specs:
            if spec.name in catalog:
                owner = catalog[spec.name].service.name
                log.warning("refusing %s from %s: already owned by %s", spec.name, service.name, owner)
                continue
            catalog[spec.name] = Entry(spec=spec, service=service)
    return catalog


async def _card_tools(url: str) -> list[SkillSpec]:
    """Describe each skill on an agent's card as a tool taking a free-text request.

    Args:
        url: Base URL of the agent.

    Returns:
        One tool per card skill, named after the skill id.
    """
    card = await a2a.fetch_card(url)
    specs = []
    for skill in card.skills:
        examples = " | ".join(skill.examples)
        description = f"{skill.description} Examples: {examples}" if examples else skill.description
        specs.append(SkillSpec(name=skill.id, description=description, input_schema=REQUEST_SCHEMA))
    return specs
