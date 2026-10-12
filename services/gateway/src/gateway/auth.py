"""Authentication at the gateway: callers must present valid user and agent tokens."""

from core.auth import AGENT_HEADER, USER_HEADER, AuthError, from_headers
from fastapi import HTTPException, Request

from gateway.settings import settings


async def caller_tokens(request: Request) -> dict[str, str]:
    """Check the caller's tokens are genuine, and hand them on for forwarding.

    Only signatures are checked here; what the tokens allow is decided by each data source.

    Args:
        request: The incoming request.

    Returns:
        The token headers, to forward to MCP servers and agents.

    Raises:
        HTTPException: 401 if a token is missing or forged.
    """
    try:
        from_headers(request.headers, settings.identity_secret)
    except AuthError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    return {AGENT_HEADER: request.headers[AGENT_HEADER], USER_HEADER: request.headers[USER_HEADER]}
