"""The context of one question: what the model sees on every turn."""

from dataclasses import dataclass, field

from core.models.chat import Message, SkillSpec


@dataclass
class Context:
    """Instructions, memory, knowledge and tools, plus the conversation of the current question."""

    instructions: str
    memory: list[Message]
    knowledge: str
    tools: list[SkillSpec]
    history: list[Message] = field(default_factory=list)

    def messages(self) -> list[Message]:
        """Assemble what is sent to the model.

        Returns:
            The system message, then the remembered exchange, then the current conversation.
        """
        system = self.instructions
        if self.knowledge:
            system += f"\n\nRelevant knowledge:\n{self.knowledge}"
        return [Message(role="system", content=system), *self.memory, *self.history]
