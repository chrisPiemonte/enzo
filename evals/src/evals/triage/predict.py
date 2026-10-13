"""Predict function for the triage eval: the real agent, running the prompt version under test."""

import asyncio
from collections.abc import Callable
from typing import Any

from enzo.bootstrap import build_agent, build_identity_provider
from enzo.config import Settings

Predict = Callable[[str, str], dict[str, Any]]


def make_predict(base: Settings, prompt_version: str, experiment: str) -> Predict:
    """Build the triage agent once and wrap it in the function mlflow.genai.evaluate calls per case.

    Args:
        base: The agent's own settings; only the prompt version, the adapters and the experiment are overridden.
        prompt_version: Version number or alias of the prompt under test.
        experiment: MLflow experiment the agent's traces go to while it is evaluated.

    Returns:
        A function taking a case's inputs (user, question) and returning what the scorers read.
    """
    settings = base.model_copy(
        update={"prompt_version": prompt_version, "prompts": "mlflow", "gateway": "http", "experiment": experiment}
    )
    agent, identities = build_agent(settings), build_identity_provider(settings)

    def predict(user: str, question: str) -> dict[str, Any]:
        """Ask one golden question as the case's user, stopping where the parts agent asks for approval.

        Args:
            user: User id the question is asked by, e.g. user:maria.
            question: The question.

        Returns:
            The answer, the parts agent's pending message (empty if none), and each tool call with its decision.
        """
        reply = asyncio.run(agent.ask(question, identities.login(user, settings.id)))
        return {
            "answer": reply.answer,
            "handoff": reply.pending.message if reply.pending else "",
            "tools": [f"{step.service}/{step.action}: {step.decision}" for step in reply.steps],
        }

    return predict
