"""Port to the store of versioned prompts."""

from typing import Protocol

from core.models.prompts import Prompt


class PromptStore(Protocol):
    """Loads a named prompt by version number or alias."""

    async def load(self, name: str, ref: str) -> Prompt:
        """Load one prompt version.

        Args:
            name: Prompt name, e.g. triage-system.
            ref: A version number ("1") or an alias ("production").

        Returns:
            The prompt text and its metadata.
        """
