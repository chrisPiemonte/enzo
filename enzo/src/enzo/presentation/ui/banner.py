"""Session banner."""

import pyfiglet
from rich.color import Color
from rich.console import Console
from rich.text import Text

TAGLINE = "field service triage agent · diagnoses instrument faults and orders the fix"
GRADIENT = (  # Monokai Pro, left to right: cyan, purple, pink, orange
    (120, 220, 232),
    (171, 157, 242),
    (255, 97, 136),
    (252, 152, 103),
)
BRIGHTNESS = 0.65  # 1.0 is the palette as is; lower is dimmer


def _blend(position: float) -> Color:
    """Pick the gradient colour at a point along the logo.

    Args:
        position: Where along the gradient, from 0.0 (start) to 1.0 (end).

    Returns:
        The blended colour.
    """
    scaled = position * (len(GRADIENT) - 1)
    index = min(int(scaled), len(GRADIENT) - 2)  # the pair of stops around this point
    start, end = GRADIENT[index], GRADIENT[index + 1]
    position = scaled - index
    red, green, blue = (round((a + (b - a) * position) * BRIGHTNESS) for a, b in zip(start, end))
    return Color.from_rgb(red, green, blue)


def _gradient_logo() -> Text:
    """Render the logo with a horizontal colour gradient.

    Returns:
        The logo as styled text.
    """
    lines = pyfiglet.figlet_format("enzo", font="slant").rstrip().splitlines()
    width = max(len(line) for line in lines) - 1
    logo = Text()
    for line in lines:
        for column, char in enumerate(line):
            logo.append(char, style=f"bold {_blend(column / width).name}")
        logo.append("\n")
    return logo


def print_banner(console: Console, user: str) -> None:
    """Print the welcome banner.

    Args:
        console: Console to print to.
        user: Logged-in user shown under the logo.
    """
    console.print(_gradient_logo(), highlight=False)
    console.print(f"  {TAGLINE}", style="italic grey85", highlight=False)
    console.print(f"  {'─' * len(TAGLINE)}", style="grey35")
    console.print(f"  logged in as [accent]{user}[/accent] · /help for commands\n", style="muted")
