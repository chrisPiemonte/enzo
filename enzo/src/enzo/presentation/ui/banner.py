"""Session banner."""

import pyfiglet
from rich.console import Console

TAGLINE = "field service triage agent · diagnoses instrument faults and orders the fix"


def print_banner(console: Console, user: str) -> None:
    """Print the welcome banner.

    Args:
        console: Console to print to.
        user: Logged-in user shown under the logo.
    """
    console.print(pyfiglet.figlet_format("enzo", font="slant").rstrip(), style="accent", highlight=False)
    console.print(f"  {TAGLINE}\n", style="bold")
    console.print(f"  logged in as [accent]{user}[/accent] · /help for commands\n", style="muted")
