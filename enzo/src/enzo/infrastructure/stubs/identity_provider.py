"""The identity provider, stubbed: signs tokens from a local file."""

from pathlib import Path

import yaml
from core.auth import AuthError, sign
from core.models.identity import AgentClaims, Identity, UserClaims

# STUB: a real deployment uses an enterprise identity provider with OAuth token exchange (user -> agent
# delegation), short-lived tokens and real authentication. Here anyone may log in as anyone in the file.


class StubIdentityProvider:
    """Reads users and agents from identity.yaml and signs their claims with the shared secret."""

    def __init__(self, path: Path, secret: str) -> None:
        """Load the identity file.

        Args:
            path: Path to identity.yaml.
            secret: Shared signing secret.
        """
        self.directory = yaml.safe_load(path.read_text())
        self.secret = secret

    def login(self, user: str, agent: str) -> Identity:
        """Issue signed tokens for a user and an agent.

        Args:
            user: User id, e.g. user:maria.
            agent: Agent id, e.g. agent:triage.

        Returns:
            The identity, carrying both tokens.

        Raises:
            AuthError: If the user or the agent is not in the file.
        """
        user_entry, agent_entry = self.directory["users"].get(user), self.directory["agents"].get(agent)
        if user_entry is None or agent_entry is None:
            raise AuthError(f"unknown {'user ' + user if user_entry is None else 'agent ' + agent}")
        user_token = sign(UserClaims(sub=user, **user_entry), self.secret)
        agent_token = sign(AgentClaims(sub=agent, **agent_entry), self.secret)
        return Identity(user=user, agent=agent, user_token=user_token, agent_token=agent_token)
