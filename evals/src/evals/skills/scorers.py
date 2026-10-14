"""Scoring for the skills eval: right skill per case, then overlap and usefulness across all cases."""

from collections import Counter
from typing import Any

from mlflow.entities import Feedback
from mlflow.genai.scorers import Scorer, scorer

Confusion = Counter[tuple[str, str]]  # (expected, picked) -> number of cases


def accuracy(outputs: dict[str, Any], expectations: dict[str, Any]) -> Feedback:
    """The model picked the expected skill, or no skill when none is expected.

    Args:
        outputs: What the predict function returned (skill).
        expectations: The golden case's expectations (skill).

    Returns:
        Pass or fail, with both skills.
    """
    expected, picked = expectations["skill"], outputs["skill"]
    return Feedback(value=picked == expected, rationale=f"expected {expected}, picked {picked}")


def case_scorers() -> list[Scorer]:
    """Wrap the per-case check as an MLflow scorer; its name is its metric and its gate.

    Returns:
        The accuracy scorer.
    """
    return [scorer(accuracy, name="accuracy")]


def separation(confusion: Confusion, skills: list[str]) -> float:
    """Share of skill pairs never confused with each other, in either direction.

    Args:
        confusion: Counts of (expected, picked) skills.
        skills: Every skill in the catalogue.

    Returns:
        1.0 when no two skills overlap.
    """
    pairs = [(a, b) for i, a in enumerate(skills) for b in skills[i + 1:]]
    confused = [pair for pair in pairs if confusion[pair] or confusion[pair[::-1]]]
    return 1 - len(confused) / len(pairs) if pairs else 1.0


def coverage(confusion: Confusion, skills: list[str]) -> float:
    """Share of skills that were the right answer, and picked, at least once.

    Args:
        confusion: Counts of (expected, picked) skills.
        skills: Every skill in the catalogue.

    Returns:
        1.0 when every skill is useful.
    """
    return sum(1 for skill in skills if confusion[(skill, skill)]) / len(skills)
