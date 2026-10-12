"""Step: retrieve long-term knowledge relevant to the question."""

from core.models.identity import Identity
from core.ports.knowledge_store import KnowledgeStore
from core.tracing import traced
from mlflow.entities import SpanType


@traced("load_knowledge", SpanType.RETRIEVER)
async def load_knowledge(knowledge: KnowledgeStore, question: str, identity: Identity) -> str:
    """Retrieve knowledge relevant to the question.

    Args:
        knowledge: Long-term knowledge store.
        question: The user's question.
        identity: Who is asking.

    Returns:
        Relevant knowledge, or an empty string.
    """
    return await knowledge.retrieve(question, identity)
