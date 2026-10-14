"""Typer entrypoint: `evals prompt <name> <version>` runs the triage eval and prints the decision."""

import typer
from enzo.config import settings as agent_settings

from evals.policy import Gate
from evals.settings import settings
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


def _print(gates: list[Gate]) -> None:
    """Print one line per gate: score, threshold, pass or fail.

    Args:
        gates: The gates' outcomes.
    """
    for gate in gates:
        score = "n/a" if gate.score is None else f"{gate.score:.0%}"
        typer.echo(f"  {'PASS' if gate.passed else 'FAIL'}  {gate.name:<15} {score:>5}  (min {gate.threshold:.0%})")
