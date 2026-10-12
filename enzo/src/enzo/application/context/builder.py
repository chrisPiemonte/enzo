"""Run the context steps in order and assemble the context of one question."""

from dataclasses import dataclass

from core.models.chat import Message
from core.models.identity import Identity
from core.ports.gateway import Gateway
from core.ports.knowledge_store import KnowledgeStore
from core.ports.memory_store import MemoryStore
from core.ports.prompt_store import PromptStore
from core.tracing import traced
from mlflow.entities import SpanType

from enzo.application.context.context import Context
from enzo.application.context.steps.instructions import load_instructions
from enzo.application.context.steps.knowledge import load_knowledge
from enzo.application.context.steps.memory import load_memory
from enzo.application.context.steps.tools import load_tools


@dataclass
class ContextBuilder:
    """Gathers instructions, memory, knowledge and tools for a question."""

    prompts: PromptStore
    prompt: tuple[str, str]  # (name, version or alias)
    memory: MemoryStore
    knowledge: KnowledgeStore
    gateway: Gateway

    @traced("build_context", SpanType.CHAIN)
    async def build(self, question: str, identity: Identity) -> Context:
        """Build the context for a new question.

        Args:
            question: The user's question.
            identity: Who is asking.

        Returns:
            The context, with the question as the start of the conversation.
        """
        return Context(
            instructions=await load_instructions(self.prompts, *self.prompt),
            memory=await load_memory(self.memory, identity),
            knowledge=await load_knowledge(self.knowledge, question, identity),
            tools=await load_tools(self.gateway, identity),
            history=[Message(role="user", content=question)],
        )
