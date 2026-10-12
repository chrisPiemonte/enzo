"""Step: recall what was said earlier in the session."""

from core.models.chat import Message
from core.models.identity import Identity
from core.ports.memory_store import MemoryStore
from core.tracing import traced
from mlflow.entities import SpanType


@traced("load_memory", SpanType.RETRIEVER)
async def load_memory(memory: MemoryStore, identity: Identity) -> list[Message]:
    """Recall the user's earlier exchange.

    Args:
        memory: Short-term memory.
        identity: Whose memory to read.

    Returns:
        Earlier messages, oldest first.
    """
    return await memory.recall(identity)
