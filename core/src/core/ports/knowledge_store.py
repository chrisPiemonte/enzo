"""Port to long-term knowledge: facts worth knowing beyond the current session."""

from typing import Protocol

from core.models.identity import Identity


class KnowledgeStore(Protocol):
    """Retrieves long-term knowledge relevant to a question."""

    async def retrieve(self, query: str, identity: Identity) -> str:
        """Find knowledge relevant to a query.

        Args:
            query: What the user asked.
            identity: Who is asking; retrieval may be limited to what they may see.

        Returns:
            Relevant knowledge as text, or an empty string.
        """
