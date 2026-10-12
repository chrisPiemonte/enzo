"""Who is acting, and the outcome of an access check."""

from typing import Literal

from pydantic import BaseModel

Decision = Literal["ALLOW", "DENY"]


class Identity(BaseModel):
    """The user and the agent carried on every hop."""

    user: str
    agent: str
