"""Step: load the system prompt."""

from core.ports.prompt_store import PromptStore
from core.tracing import traced
from mlflow.entities import SpanType


@traced("load_instructions", SpanType.CHAIN)
async def load_instructions(prompts: PromptStore, name: str, ref: str) -> str:
    """Load the agent's instructions from the prompt store.

    Args:
        prompts: Store of versioned prompts.
        name: Prompt name.
        ref: Version number or alias.

    Returns:
        The prompt text.
    """
    return (await prompts.load(name, ref)).text
