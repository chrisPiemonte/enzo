"""Long-term knowledge that knows nothing yet."""

from core.models.identity import Identity

# MOCK: no knowledge base exists yet.


class MockKnowledgeStore:
    """Always returns no knowledge."""

    async def retrieve(self, query: str, identity: Identity) -> str:
        """Return no knowledge.

        Args:
            query: Ignored.
            identity: Ignored.

        Returns:
            An empty string.
        """
        return ""
