"""Short-term memory kept in the process: the last exchange per user."""

from core.models.chat import Message
from core.models.identity import Identity

# MOCK: lost on exit, and only the last exchange is kept.


class MockMemoryStore:
    """Remembers each user's last question and answer."""

    def __init__(self) -> None:
        """Start with no memories."""
        self.last: dict[str, list[Message]] = {}

    async def recall(self, identity: Identity) -> list[Message]:
        """Return the user's last exchange.

        Args:
            identity: Whose memory to read.

        Returns:
            The last question and answer, or nothing.
        """
        return self.last.get(identity.user, [])

    async def remember(self, identity: Identity, messages: list[Message]) -> None:
        """Replace the user's last exchange.

        Args:
            identity: Whose memory to write.
            messages: The exchange to remember.
        """
        self.last[identity.user] = messages
