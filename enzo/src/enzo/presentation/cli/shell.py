"""Interactive shell: slash commands, questions, and conversations handed off to remote agents."""

from core.auth import AuthError
from core.models.identity import Identity
from core.models.reply import AgentReply, ToolCall
from core.ports.gateway import GatewayError
from core.ports.identity_provider import IdentityProvider
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from enzo.application.loop import TriageAgent
from enzo.presentation.ui.banner import print_banner
from enzo.presentation.ui.theme import PROMPT_HTML, THEME

console = Console(theme=THEME)

HELP = "/login <user>  ·  /agent <agent>  ·  /replay <trace_id>  ·  /help  ·  /exit"


async def run_shell(agent: TriageAgent, provider: IdentityProvider, identity: Identity) -> None:
    """Run the interactive loop until the user exits.

    Args:
        agent: The triage agent answering questions.
        provider: Issues tokens when the user or agent changes.
        identity: User and agent the session starts with.
    """
    session: PromptSession[str] = PromptSession()
    agent.on_step = _print_step  # steps appear live, while the spinner runs
    print_banner(console, f"{identity.user} · {identity.agent}")

    while True:
        try:
            text = (await session.prompt_async(HTML(PROMPT_HTML))).strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not text:
            continue
        if text in ("/exit", "/quit"):
            break
        if text == "/help":
            console.print(HELP, style="muted")
        elif text.startswith(("/login ", "/agent ")):
            identity = _switch(provider, identity, text)
        elif text.startswith("/replay"):
            console.print("[muted]replay: not implemented (mock)[/muted]")
        elif text.startswith("/"):
            console.print(f"[deny]unknown command[/deny] · {HELP}")
        else:
            try:
                with _working("enzo is thinking…"):
                    reply = await agent.ask(text, identity)
                _print_reply(reply)
                while reply.pending:  # a remote agent waits for the user; answers go back through the agent
                    prompt = HTML(f"<ansicyan>  {reply.pending.agent} ❯ </ansicyan>")
                    answer = (await session.prompt_async(prompt)).strip()
                    if not answer or answer.startswith("/"):
                        console.print(f"[muted]{reply.pending.agent} is waiting: answer approve or reject[/muted]")
                        continue
                    with _working(f"{reply.pending.agent} is working…"):
                        reply = await agent.answer(reply.trace_id, answer)
                    _print_reply(reply)
            except GatewayError as error:
                console.print(f"[deny]gateway error[/deny] {error}")
            console.print("\n")  # blank lines between one exchange and the next


def _print_reply(reply: AgentReply) -> None:
    """Print the model's answer, and the question of a remote agent waiting for the user (steps print live).

    Args:
        reply: The agent's reply.
    """
    if reply.answer.strip():
        title = f"triage · {reply.model}"
        console.print(Panel(reply.answer, title=title, subtitle=f"trace {reply.trace_id}", border_style="accent"))
    elif not reply.pending:
        console.print(f"  [muted]triage · {reply.model} · no answer · {reply.trace_id}[/muted]")
    elif not any(step.action.startswith("reply:") for step in reply.steps):  # handed over without explaining
        console.print(f"  [muted]triage · handing over to {reply.pending.agent} (no explanation)[/muted]")
    if reply.pending:
        console.print(f"[accent]{reply.pending.agent}[/accent] › {reply.pending.message}")


def _print_step(step: ToolCall) -> None:
    """Print one step as it happens.

    Args:
        step: The step: what was called, and whether it was allowed.
    """
    style = "allow" if step.decision == "ALLOW" else "deny"
    console.print(f"  → {step.service:<18} {step.action:<30} [{style}]{step.decision}[/{style}]")

def _working(label: str) -> Live:
    """Show an indented spinner, set apart from the steps above it, until the block ends.

    Args:
        label: What is happening, shown next to the spinner.

    Returns:
        The live display, to use as a context manager.
    """
    spinner = Spinner("dots", text=Text(f" {label}", style="muted"), style="accent")
    return Live(Padding(spinner, (1, 0, 0, 2)), console=console, transient=True)


def _switch(provider: IdentityProvider, identity: Identity, command: str) -> Identity:
    """Log in as another user (/login) or act through another agent (/agent), with fresh tokens.

    Args:
        provider: Issues the tokens.
        identity: The current identity.
        command: "/login <user>" or "/agent <agent>".

    Returns:
        The new identity, or the current one if the name is unknown.
    """
    verb, name = command.split(maxsplit=1)
    user, agent = (f"user:{name}", identity.agent) if verb == "/login" else (identity.user, f"agent:{name}")
    try:
        identity = provider.login(user, agent)
    except AuthError as error:
        console.print(f"[deny]{error}[/deny]")
        return identity
    console.print(f"logged in as [accent]{identity.user}[/accent] · acting through [accent]{identity.agent}[/accent]")
    return identity
