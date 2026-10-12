"""Typer entrypoint: `enzo` builds the agent and opens the interactive shell."""

import asyncio

import typer

from enzo import __version__
from enzo.bootstrap import build_agent, build_identity_provider
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
    provider = build_identity_provider(settings)
    identity = provider.login(settings.user, settings.id)
    asyncio.run(run_shell(build_agent(settings), provider, identity))
