"""Signed identity tokens: sign, verify, and carry them in HTTP headers."""

from collections.abc import Mapping
from typing import TypeVar

import jwt
from pydantic import BaseModel, ValidationError

from core.models.identity import AgentClaims, Identity, UserClaims

AGENT_HEADER = "authorization"  # "Bearer <agent token>"
USER_HEADER = "x-user-token"
ALGORITHM = "HS256"

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
