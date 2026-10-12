"""The port every provider adapter implements."""

from typing import Protocol

from core.models.chat import Completion, Message, SkillSpec


class ProviderError(RuntimeError):
    """The provider could not be reached or returned an error."""


class Provider(Protocol):
    """A model provider behind the gateway, speaking one API format."""

    async def complete(self, model: str, messages: list[Message], tools: list[SkillSpec]) -> Completion:
        """Complete a conversation.

        Args:
            model: Provider-side model name.
            messages: The conversation so far.
            tools: Skills the model may call.

        Returns:
            The model's text and/or skill calls.

        Raises:
            ProviderError: If the provider fails.
        """
