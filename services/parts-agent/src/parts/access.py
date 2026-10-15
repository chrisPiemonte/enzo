"""Who may ask for an order, and who may approve one."""

import os
from collections.abc import Mapping

from core.auth import AuthError, authorize, from_headers

SECRET = os.environ["IDENTITY_SECRET"]


def check_request(headers: Mapping[str, str], account: str) -> None:
    """Allow an order request only from an agent with orders:request, for a user entitled to the account.

    Args:
        headers: Request headers carrying both tokens.
        account: Customer account of the instrument.

    Raises:
        PermissionError: With the reason, if either check fails.
    """
    authorize(headers, SECRET, "orders:request", account)


def check_approval(headers: Mapping[str, str], account: str) -> None:
    """Allow an approval only from a user who may approve orders for the account.

    Args:
        headers: Request headers carrying both tokens.
        account: Customer account of the instrument.

    Raises:
        PermissionError: With the reason, if the user may not approve.
    """
    try:
        user, _ = from_headers(headers, SECRET)
    except AuthError as error:
        raise PermissionError(str(error)) from error
    if not user.approve_orders or account not in user.accounts:
        raise PermissionError(f"user {user.sub} may not approve orders for {account}")
