"""Predict function for the skills eval: one model call that picks a tool from the catalogue, executing nothing."""

import asyncio
from collections.abc import Callable
from typing import Any

from core.models.chat import Message, SkillSpec
from core.models.identity import Identity
from core.ports.gateway import Gateway
from core.tracing import traced
from mlflow.entities import SpanType

NONE = "none"  # the model called no tool

Predict = Callable[[str], dict[str, Any]]  # request -> {"skill": name}


def make_predict(gateway: Gateway, identity: Identity, rule: str, catalogue: list[SkillSpec]) -> Predict:
    """Wrap one routing call in the function mlflow.genai.evaluate calls per case.

    Args:
        gateway: Gateway adapter, bound to the model alias that routes.
        identity: The eval harness's own identity.
        rule: The router's instructions.
        catalogue: The skills offered as tools, possibly with a candidate added.

    Returns:
        A function taking a case's request and returning the skill the model picked.
    """

    @traced("route", SpanType.CHAIN)  # one trace per case, which the eval attaches its scores to
    def predict(request: str) -> dict[str, Any]:
        """Ask the model which tool it would call for one request.

        Args:
            request: The engineer's request.

        Returns:
            The first tool the model called, or none.
        """
        messages = [Message(role="system", content=rule), Message(role="user", content=request)]
        completion = asyncio.run(gateway.complete(messages, catalogue, identity))
        return {"skill": completion.skill_calls[0].name if completion.skill_calls else NONE}

    return predict
