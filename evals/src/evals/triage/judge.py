"""G3, an LLM judge: grades one answer against a written rule, calling the model through the gateway."""

import asyncio
import re
from typing import Any

from core.models.chat import Message
from core.models.identity import Identity
from core.ports.gateway import Gateway
from mlflow.entities import AssessmentSource, Feedback
from mlflow.genai.scorers import Scorer, scorer

VERDICT = re.compile(r"\b(PASS|FAIL)\b")


def make_judge(name: str, rule: str, gateway: Gateway, identity: Identity) -> Scorer:
    """Build a scorer that asks a model, behind a gateway alias, whether an answer follows a rule.

    Args:
        name: Scorer name; it becomes the metric and the gate.
        rule: The judge's instructions, ending with a request for a PASS or FAIL line.
        gateway: Gateway adapter, bound to the judge's model alias.
        identity: The judge's own user and agent, signed like any other caller's.

    Returns:
        The judge as an MLflow scorer.
    """

    def judge(outputs: dict[str, Any]) -> Feedback:
        """Ask the judge model about one answer; its last PASS or FAIL is the verdict.

        Args:
            outputs: What the predict function returned (answer, handoff, tools).

        Returns:
            The verdict with the judge's reasoning, or an error if the reply holds no verdict.
        """
        messages = [
            Message(role="system", content=rule),
            Message(role="user", content=f"{outputs['answer']}\n{outputs['handoff']}".strip()),
        ]
        completion = asyncio.run(gateway.complete(messages, [], identity))
        text = (completion.text or "").strip()
        source = AssessmentSource(source_type="LLM_JUDGE", source_id=f"{completion.provider}/{completion.model}")
        if not (verdicts := VERDICT.findall(text)):
            return Feedback(error=f"no PASS or FAIL in the judge's reply: {text[:200]}", source=source)
        return Feedback(value=verdicts[-1] == "PASS", rationale=text, source=source)

    return scorer(judge, name=name)
