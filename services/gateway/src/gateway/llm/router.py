"""Turn a completion request into the provider and model that will answer it."""

from core.models.chat import CompletionRequest
from pydantic import BaseModel

from gateway.llm.config import GatewayConfig, ProviderConfig


class Route(BaseModel):
    """The resolved provider and model for one request."""

    provider: str
    config: ProviderConfig
    model: str


class RouteError(LookupError):
    """The request names an alias or provider the gateway does not know."""


def resolve(request: CompletionRequest, config: GatewayConfig) -> Route:
    """Pick the provider and model for a request: alias first, then explicit overrides.

    Args:
        request: The incoming completion request.
        config: The gateway's providers and aliases.

    Returns:
        The provider and model to call.

    Raises:
        RouteError: If the alias or the overriding provider is unknown, or no model can be determined.
    """
    alias = config.aliases.get(request.model)
    provider = request.provider or (alias.provider if alias else None)
    model = request.provider_model or (alias.model if alias else None)
    if provider is None or model is None:
        raise RouteError(f"unknown model alias {request.model!r}")
    if provider not in config.providers:
        raise RouteError(f"unknown provider {provider!r}")
    return Route(provider=provider, config=config.providers[provider], model=model)
