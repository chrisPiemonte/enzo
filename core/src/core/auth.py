"""Signed identity tokens: sign, verify, and carry them in HTTP headers."""

from collections.abc import Mapping
from typing import TypeVar

import jwt
from pydantic import BaseModel, ValidationError

from core.models.identity import AgentClaims, Identity, UserClaims

AGENT_HEADER = "authorization"  # "Bearer <agent token>"
USER_HEADER = "x-user-token"
ALGORITHM = "HS256"
DENIED = "access denied"  # prefix of every denial message, so callers can tell a denial from other failures

C = TypeVar("C", bound=BaseModel)


class AuthError(ValueError):
    """A token is missing, forged, or malformed."""


def sign(claims: BaseModel, secret: str) -> str:
    """Sign claims into a token.

    Args:
        claims: User or agent claims.
        secret: Shared signing secret.

    Returns:
        The signed token.
    """
    return jwt.encode(claims.model_dump(), secret, algorithm=ALGORITHM)


def verify(token: str, secret: str, model: type[C]) -> C:
    """Check a token's signature and read its claims.

    Args:
        token: The signed token.
        secret: Shared signing secret.
        model: Claims model to read the token into.

    Returns:
        The verified claims.

    Raises:
        AuthError: If the token is forged or its claims do not fit the model.
    """
    try:
        return model.model_validate(jwt.decode(token, secret, algorithms=[ALGORITHM]))
    except (jwt.InvalidTokenError, ValidationError) as error:
        raise AuthError(f"invalid token: {error}") from error


def to_headers(identity: Identity) -> dict[str, str]:
    """Put an identity's tokens into HTTP headers.

    Args:
        identity: The identity carrying the tokens.

    Returns:
        The headers.
    """
    return {AGENT_HEADER: f"Bearer {identity.agent_token}", USER_HEADER: identity.user_token}


def from_headers(headers: Mapping[str, str], secret: str) -> tuple[UserClaims, AgentClaims]:
    """Verify the tokens of an incoming request.

    Args:
        headers: Request headers (case-insensitive mapping, or lower-case keys).
        secret: Shared signing secret.

    Returns:
        The verified user and agent claims.

    Raises:
        AuthError: If either token is missing or invalid.
    """
    agent_token = headers.get(AGENT_HEADER, "").removeprefix("Bearer ").strip()
    user_token = headers.get(USER_HEADER, "")
    if not agent_token or not user_token:
        raise AuthError("missing user or agent token")
    return verify(user_token, secret, UserClaims), verify(agent_token, secret, AgentClaims)


def authorize(headers: Mapping[str, str] | None, secret: str, scope: str, account: str | None = None) -> None:
    """Allow a call only if the agent holds the scope and the user is entitled to the account.

    Permission is the overlap of both: a capable agent cannot reach data its user may not see, and an entitled
    user cannot reach it through an agent without the scope.

    Args:
        headers: The request headers carrying both tokens.
        secret: Shared signing secret.
        scope: Scope the agent needs, e.g. telemetry:read.
        account: Customer account the data belongs to; None for data not tied to an account.

    Raises:
        PermissionError: With the reason, if a token is missing or invalid, or either check fails.
    """
    try:
        user, agent = from_headers(headers or {}, secret)
    except AuthError as error:
        raise PermissionError(str(error)) from error
    if scope not in agent.scopes:
        raise PermissionError(f"agent {agent.sub} lacks {scope}")
    if account is not None and account not in user.accounts:
        raise PermissionError(f"user {user.sub} is not entitled to {account}")
