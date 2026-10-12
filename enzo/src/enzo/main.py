"""Typer entrypoint: `enzo` builds the agent and opens the interactive shell."""

import asyncio

import typer
from core.models.identity import Identity

from enzo import __version__
from enzo.bootstrap import build_agent
from enzo.config import settings
from enzo.presentation.cli.shell import run_shell

app = typer.Typer(name="enzo", add_completion=False, pretty_exceptions_enable=False)


@app.command()
def main(version: bool = typer.Option(False, "--version", "-v", help="Show version and exit.")) -> None:
    """Start the Enzo triage shell.

    Args:
        version: Print the version and exit instead of starting the shell.

    Raises:
        typer.Exit: After printing the version.
    """
    if version:
        typer.echo(f"enzo {__version__}")
        raise typer.Exit()
    identity = Identity(user=settings.user, agent=settings.id)
    asyncio.run(run_shell(build_agent(settings), identity))
