"""Step: retrieve the tools every running service offers, through the gateway."""

from core.models.chat import SkillSpec
from core.ports.gateway import Gateway
from core.tracing import traced
from mlflow.entities import SpanType


@traced("load_tools", SpanType.CHAIN)
async def load_tools(gateway: Gateway) -> list[SkillSpec]:
    """Retrieve the gateway's current tool catalogue: MCP tools and agent card skills.

    Args:
        gateway: The gateway.

    Returns:
        The tools to offer the model.
    """
    return await gateway.list_tools()
