"""A versioned prompt."""

from pydantic import BaseModel


class Prompt(BaseModel):
    """One version of a named prompt."""

    name: str
    version: int
    description: str
    text: str
