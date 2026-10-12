"""Composition root: the only module that knows the concrete adapters."""

from core.adapters.file_prompt_store import FilePromptStore
from core.adapters.http_gateway import HttpGateway
from core.ports.gateway import Gateway

from enzo.application.actions import Actions
from enzo.application.context.builder import ContextBuilder
from enzo.application.loop import TriageAgent
from enzo.config import Settings
from enzo.infrastructure.mocks.audit import MockAuditLog
from enzo.infrastructure.mocks.gateway import MockGateway
from enzo.infrastructure.mocks.knowledge import MockKnowledgeStore
from enzo.infrastructure.mocks.memory import MockMemoryStore


def build_agent(settings: Settings) -> TriageAgent:
    """Build the triage agent with the adapters chosen in settings.

    Args:
        settings: Agent settings, including one adapter switch per port.

    Returns:
        A ready-to-use triage agent.
    """
    gateway, memory = _gateway(settings), MockMemoryStore()
    builder = ContextBuilder(
        prompts=FilePromptStore(settings.prompts_dir),
        prompt=(settings.prompt, settings.prompt_version),
        memory=memory,
        knowledge=MockKnowledgeStore(),
        gateway=gateway,
    )
    return TriageAgent(builder=builder, gateway=gateway, actions=Actions(gateway), memory=memory, audit=MockAuditLog())


def _gateway(settings: Settings) -> Gateway:
    """Pick the gateway adapter.

    Args:
        settings: Agent settings.

    Returns:
        The HTTP adapter, or the scripted mock of the whole gateway.
    """
    match settings.gateway:
        case "http":
            return HttpGateway(settings.gateway_url, settings.model_alias)
        case "mock":
            return MockGateway()
