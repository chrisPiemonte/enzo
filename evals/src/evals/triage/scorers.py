"""Code scorers for the triage eval: deterministic checks of one answer against its golden expectations."""

import re
from typing import Any

from mlflow.entities import Feedback
from mlflow.genai.scorers import Scorer, scorer

PART = re.compile(r"\bP-\d+\b")
RECORD = re.compile(r"\b[a-z]{3}-\d+-\d+\b")  # e.g. tel-1001-0412, svc-1001-007


def grounding(outputs: dict[str, Any], expectations: dict[str, Any]) -> Feedback:
    """G1: the answer names exactly the part the manual lists for this model, or no part when none is expected.

    Args:
        outputs: What the predict function returned (answer, handoff, tools).
        expectations: The golden case's expectations (part, records).

    Returns:
        Pass or fail, with the parts found.
    """
    found, expected = set(PART.findall(_text(outputs))), expectations["part"]
    passed = found == ({expected} if expected else set())
    return Feedback(value=passed, rationale=f"expected {expected or 'no part'}, found {sorted(found) or 'none'}")


def evidence(outputs: dict[str, Any], expectations: dict[str, Any]) -> Feedback:
    """G2: the answer cites records, and only records the tools could have returned for this case.

    Args:
        outputs: What the predict function returned.
        expectations: The golden case's expectations; an empty records list means nothing may be cited.

    Returns:
        Pass or fail, with the records cited.
    """
    cited, allowed = set(RECORD.findall(_text(outputs))), set(expectations["records"])
    passed = cited <= allowed and bool(cited) == bool(allowed)
    return Feedback(value=passed, rationale=f"cited {sorted(cited) or 'none'}, allowed {sorted(allowed) or 'none'}")


def history(outputs: dict[str, Any]) -> Feedback:
    """G4: the agent consulted the service history (prompt v4, rule 6), whether or not the call was allowed.

    Args:
        outputs: What the predict function returned.

    Returns:
        Pass or fail, with the tools called.
    """
    tools: list[str] = outputs["tools"]
    passed = any("get_service_history" in tool for tool in tools)
    return Feedback(value=passed, rationale=f"tools called: {tools or 'none'}")


def _text(outputs: dict[str, Any]) -> str:
    """Join what the user reads: the agent's answer and the parts agent's pending message.

    Args:
        outputs: What the predict function returned.

    Returns:
        Both texts, one after the other.
    """
    return f"{outputs['answer']}\n{outputs['handoff']}"


def code_scorers() -> list[Scorer]:
    """Wrap the code checks as MLflow scorers; the name of each becomes its metric and its gate.

    Returns:
        The grounding, evidence and history scorers.
    """
    return [scorer(check, name=check.__name__) for check in (grounding, evidence, history)]
