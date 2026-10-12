"""Build the provider adapter for a resolved route."""

from gateway.llm.providers.anthropic_provider import AnthropicProvider
from gateway.llm.providers.mock_provider import MockProvider
from gateway.llm.providers.openai_provider import OpenAIProvider
from gateway.llm.providers.provider import Provider
from gateway.llm.router import Route


def build_provider(route: Route) -> Provider:
    """Create the adapter matching the route's API format.

    Args:
        route: The resolved provider and model.

    Returns:
        A provider adapter.
    """
    match route.config.kind:
        case "openai":
            return OpenAIProvider(route.provider, route.config.base_url)
        case "anthropic":
            return AnthropicProvider(route.provider, route.config.base_url)
        case "mock":
            return MockProvider(route.provider)
