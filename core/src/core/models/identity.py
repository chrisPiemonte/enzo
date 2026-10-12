"""Who is acting, what they may do, and the outcome of an access check."""

from typing import Literal

from pydantic import BaseModel

Decision = Literal["ALLOW", "DENY"]


class UserClaims(BaseModel):
    """What a user may see and do, as signed into the user token."""

    sub: str
    accounts: list[str]
    approve_orders: bool = False


class AgentClaims(BaseModel):
    """What an agent may do, as signed into the agent token."""

    sub: str
    scopes: list[str]


class Identity(BaseModel):
    """The user and the agent carried on every hop, with their signed tokens."""

    user: str
    agent: str
    user_token: str = ""
    agent_token: str = ""
