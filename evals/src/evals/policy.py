"""Promotion policy: minimum pass rates per gate, and the decision that follows from an eval's metrics."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class Policy(BaseModel):
    """Minimum pass rate per gate (scorer name), for one golden set version."""

    golden: str
    gates: dict[str, float]


class Gate(BaseModel):
    """One gate's outcome."""

    name: str
    score: float | None  # None: the scorer produced no result at all, e.g. the judge never gave a verdict
    threshold: float

    @property
    def passed(self) -> bool:
        """Whether the score reaches the threshold; a missing score never does."""
        return self.score is not None and self.score >= self.threshold


def load(path: Path) -> Policy:
    """Read a policy file.

    Args:
        path: Path to policy.yaml.

    Returns:
        The policy.
    """
    return Policy.model_validate(yaml.safe_load(path.read_text()))


def decide(policy: Policy, metrics: dict[str, float]) -> list[Gate]:
    """Check each gate against the eval's metrics; the version is certified only if all of them pass.

    Args:
        policy: The promotion policy.
        metrics: MLflow eval metrics, e.g. {"grounding/mean": 1.0}.

    Returns:
        One outcome per gate, in policy order.
    """
    return [Gate(name=name, score=metrics.get(f"{name}/mean"), threshold=threshold)
            for name, threshold in policy.gates.items()]
