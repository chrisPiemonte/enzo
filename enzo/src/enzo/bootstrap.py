"""Composition root: the only module that knows the concrete adapters."""

from core.adapters.file_prompt_store import FilePromptStore
from core.adapters.http_gateway import HttpGateway
from core.adapters.mlflow_prompt_store import MlflowPromptStore
from core.ports.gateway import Gateway
from core.ports.identity_provider import IdentityProvider
from core.ports.prompt_store import PromptStore
from core.tracing import setup as setup_tracing

from enzo.application.actions import Actions
from enzo.application.context.builder import ContextBuilder
from enzo.application.loop import TriageAgent
from enzo.config import Settings
from enzo.infrastructure.mocks.audit import MockAuditLog
from enzo.infrastructure.mocks.gateway import MockGateway
from enzo.infrastructure.mocks.knowledge import MockKnowledgeStore
from enzo.infrastructure.mocks.memory import MockMemoryStore
from enzo.infrastructure.stubs.identity_provider import StubIdentityProvider


def build_agent(settings: Settings) -> TriageAgent:
    """Build the triage agent with the adapters chosen in settings.

    Args:
        settings: Agent settings, including one adapter switch per port.

    Returns:
        A ready-to-use triage agent.
    """
    setup_tracing(settings.mlflow_url, settings.experiment)
    gateway, memory = _gateway(settings), MockMemoryStore()
    builder = ContextBuilder(
        prompts=_prompts(settings),
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


def _prompts(settings: Settings) -> PromptStore:
    """Pick the prompt store adapter.

    Args:
        settings: Agent settings.

    Returns:
        The MLflow prompt registry, or the prompt files it is synced from.
    """
    match settings.prompts:
        case "mlflow":
            return MlflowPromptStore()
        case "file":
            return FilePromptStore(settings.prompts_dir)


def build_identity_provider(settings: Settings) -> IdentityProvider:
    """Build the identity provider.

    Args:
        settings: Agent settings with the identity file and the shared secret.

    Returns:
        The stub identity provider.
    """
    return StubIdentityProvider(settings.identity_file, settings.identity_secret)
