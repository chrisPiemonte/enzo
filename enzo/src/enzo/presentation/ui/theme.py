"""Rich theme and prompt style."""

from rich.theme import Theme

THEME = Theme(
    {
        "accent": "bright_cyan",
        "muted": "grey70",
        "allow": "bright_green",
        "deny": "bright_red",
    }
)

PROMPT_HTML = "<ansicyan><b> ❯ </b></ansicyan>"
