"""A provider that answers with canned text, for working offline."""

from core.models.chat import Completion, Message, SkillSpec


class MockProvider:
    """Returns a fixed answer without calling any model."""

    def __init__(self, name: str) -> None:
        """Create the mock provider.

        Args:
            name: Provider name reported in completions.
        """
        self.name = name

    async def complete(self, model: str, messages: list[Message], tools: list[SkillSpec]) -> Completion:
        """Return a canned completion.

        Args:
            model: Provider-side model name, echoed back.
            messages: Ignored.
            tools: Ignored.

        Returns:
            A fixed completion with no skill calls.
        """
        return Completion(model=model, provider=self.name, text="Mock completion from the gateway.")
