"""Interactive shell: slash commands, questions, and conversations handed off to remote agents."""

from core.models.identity import Identity
from core.models.reply import AgentReply, ToolCall
from core.ports.gateway import GatewayError
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel

from enzo.application.loop import TriageAgent
from enzo.presentation.ui.banner import print_banner
from enzo.presentation.ui.theme import PROMPT_HTML, THEME

console = Console(theme=THEME)

HELP = "/login <user>  ·  /replay <trace_id>  ·  /help  ·  /exit"


async def run_shell(agent: TriageAgent, identity: Identity) -> None:
    """Run the interactive loop until the user exits.

    Args:
        agent: The triage agent answering questions.
        identity: User and agent the session starts with.
    """
    session: PromptSession[str] = PromptSession()
    agent.on_step = _print_step  # steps appear live, while the spinner runs
    print_banner(console, identity.user)

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
        elif text.startswith("/login "):
            identity = identity.model_copy(update={"user": f"user:{text.split(maxsplit=1)[1]}"})
            console.print(f"logged in as [accent]{identity.user}[/accent]")
        elif text.startswith("/replay"):
            console.print("[muted]replay: not implemented (mock)[/muted]")
        elif text.startswith("/"):
            console.print(f"[deny]unknown command[/deny] · {HELP}")
        else:
            try:
                with console.status("[muted]enzo is thinking…[/muted]", spinner="dots"):
                    reply = await agent.ask(text, identity)
                _print_reply(reply)
                while reply.pending:  # a remote agent waits for the user; answers go back through the agent
                    prompt = HTML(f"<ansicyan>  {reply.pending.agent} ❯ </ansicyan>")
                    answer = (await session.prompt_async(prompt)).strip()
                    if not answer or answer.startswith("/"):
                        console.print(f"[muted]{reply.pending.agent} is waiting: answer approve or reject[/muted]")
                        continue
                    with console.status(f"[muted]{reply.pending.agent} is working…[/muted]", spinner="dots"):
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
