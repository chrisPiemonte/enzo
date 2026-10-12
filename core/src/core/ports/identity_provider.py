"""Port to the identity provider: who is logged in, and their signed tokens."""

from typing import Protocol

from core.models.identity import Identity


class IdentityProvider(Protocol):
    """Logs a user in together with the agent acting for them."""

    def login(self, user: str, agent: str) -> Identity:
        """Issue signed tokens for a user and an agent.

        Args:
            user: User id, e.g. user:maria.
            agent: Agent id, e.g. agent:triage.

        Returns:
            The identity, carrying both tokens.

        Raises:
            AuthError: If the user or the agent is unknown.
        """
