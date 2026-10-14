"""Typer entrypoint: `evals prompt` (is a prompt fit for production) and `evals skills` (is the registry sound)."""

import typer
from enzo.config import settings as agent_settings

from evals.policy import Gate
from evals.settings import settings
from evals.skills.predict import NONE
from evals.skills.run import evaluate_skills
from evals.skills.scorers import Confusion
from evals.triage.run import evaluate_prompt

app = typer.Typer(name="evals", add_completion=False, pretty_exceptions_enable=False)


@app.callback()
def main() -> None:
    """Enzo eval harness: golden sets, gates and promotion decisions, recorded in MLflow."""


@app.command()
def prompt(
    name: str = typer.Argument(help="Prompt name, e.g. triage-system."),
    version: int = typer.Argument(help="Prompt version number to evaluate."),
    promote: bool = typer.Option(False, "--promote", help="If certified, point the production alias at it."),
) -> None:
    """Evaluate one prompt version against the golden set and decide by policy.

    Args:
        name: Prompt name.
        version: Prompt version number.
        promote: Move the production alias if every gate passes.

    Raises:
        typer.Exit: With code 1 if the version is blocked, so scripts and CI can stop on it.
    """
    gates = evaluate_prompt(name, version, promote, settings, agent_settings)
    _print(gates)
    blocked = [gate.name for gate in gates if not gate.passed]
    if blocked:
        typer.echo(f"\n{name} v{version}: BLOCKED by {', '.join(blocked)}")
        raise typer.Exit(1)
    typer.echo(f"\n{name} v{version}: CERTIFIED" + (f", now {name}@production" if promote else ""))


@app.command()
def skills(
    candidate: str | None = typer.Option(None, "--candidate", help="A skill from candidates.yaml to try out."),
) -> None:
    """Check the registered skills are distinct and useful, optionally with a candidate skill added.

    Args:
        candidate: Candidate skill name, or None for the registry as it is.

    Raises:
        typer.Exit: With code 1 if the catalogue is blocked.
    """
    gates, confusion = evaluate_skills(candidate, settings, agent_settings)
    _print_confusion(confusion)
    _print(gates)
    label = "registry" + (f" + {candidate}" if candidate else "")
    blocked = [gate.name for gate in gates if not gate.passed]
    if blocked:
        typer.echo(f"\n{label}: BLOCKED by {', '.join(blocked)}")
        raise typer.Exit(1)
    typer.echo(f"\n{label}: CERTIFIED")


def _print_confusion(confusion: Confusion) -> None:
    """Print each expected skill with what the model picked for it; anything off the diagonal is an overlap.

    Args:
        confusion: Counts of (expected, picked).
    """
    typer.echo("")
    for expected in sorted({exp for exp, _ in confusion}, key=lambda name: (name == NONE, name)):
        picks = ", ".join(f"{picked} x{count}" for (exp, picked), count in confusion.items() if exp == expected)
        marker = "  " if all(picked == expected for (exp, picked) in confusion if exp == expected) else "!!"
        typer.echo(f"  {marker} {expected:<31} -> {picks}")
    typer.echo("")


def _print(gates: list[Gate]) -> None:
    """Print one line per gate: score, threshold, pass or fail.

    Args:
        gates: The gates' outcomes.
    """
    for gate in gates:
        score = "n/a" if gate.score is None else f"{gate.score:.0%}"
        typer.echo(f"  {'PASS' if gate.passed else 'FAIL'}  {gate.name:<15} {score:>5}  (min {gate.threshold:.0%})")
