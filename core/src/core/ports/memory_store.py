"""Port to short-term memory: what was said earlier in the session."""

from typing import Protocol

from core.models.chat import Message
from core.models.identity import Identity


class MemoryStore(Protocol):
    """Keeps recent exchanges per user so follow-up questions have context."""

    async def recall(self, identity: Identity) -> list[Message]:
        """Return the remembered messages for a user.

        Args:
            identity: Whose memory to read.

        Returns:
            Earlier messages, oldest first.
        """

    async def remember(self, identity: Identity, messages: list[Message]) -> None:
        """Store the messages of a finished exchange.

        Args:
            identity: Whose memory to write.
            messages: The exchange to remember.
        """
