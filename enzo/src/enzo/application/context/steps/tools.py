"""Step: retrieve the tools every running service offers, through the gateway."""

from core.models.chat import SkillSpec
from core.models.identity import Identity
from core.ports.gateway import Gateway
from core.tracing import traced
from mlflow.entities import SpanType


@traced("load_tools", SpanType.CHAIN)
async def load_tools(gateway: Gateway, identity: Identity) -> list[SkillSpec]:
    """Retrieve the gateway's current tool catalogue: MCP tools and agent card skills.

    Args:
        gateway: The gateway.
        identity: Who is asking.

    Returns:
        The tools to offer the model.
    """
    return await gateway.list_tools(identity)
