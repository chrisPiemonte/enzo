"""Adapter for providers speaking the Anthropic Messages API."""

import anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolParam, ToolResultBlockParam, ToolUseBlockParam
from core.models.chat import Completion, Message, SkillCall, SkillSpec

from gateway.llm.providers.provider import ProviderError

# STUB: Ollama ignores the key; the real Anthropic API needs one from settings.
API_KEY = "unused"
MAX_TOKENS = 4096


class AnthropicProvider:
    """Calls an Anthropic-compatible endpoint and translates to and from the shared chat models."""

    def __init__(self, name: str, base_url: str) -> None:
        """Create the adapter.

        Args:
            name: Provider name reported in completions.
            base_url: Endpoint of the Anthropic-compatible API.
        """
        self.name = name
        self.client = anthropic.AsyncAnthropic(base_url=base_url, api_key=API_KEY)

    async def complete(self, model: str, messages: list[Message], tools: list[SkillSpec]) -> Completion:
        """Complete a conversation through the Anthropic API.

        Args:
            model: Provider-side model name.
            messages: The conversation so far.
            tools: Skills the model may call.

        Returns:
            The model's text and/or skill calls.

        Raises:
            ProviderError: If the endpoint fails or is unreachable.
        """
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=system or anthropic.omit,
                messages=_to_anthropic_messages(messages),
                tools=[_to_anthropic_tool(tool) for tool in tools],
                extra_body={"temperature": 0},  # the SDK no longer exposes temperature; Ollama still honours it
            )
        except anthropic.AnthropicError as error:
            raise ProviderError(f"{self.name}: {error}") from error
        text = "".join(block.text for block in response.content if block.type == "text")
        calls = [
            SkillCall(id=block.id, name=block.name, args=dict(block.input))
            for block in response.content
            if block.type == "tool_use"
        ]
        return Completion(model=model, provider=self.name, text=text or None, skill_calls=calls)


def _to_anthropic_messages(messages: list[Message]) -> list[MessageParam]:
    """Translate shared messages into Anthropic turns.

    System messages are dropped (they travel separately), and consecutive tool results are merged into
    one user turn, as the Messages API requires.

    Args:
        messages: The shared conversation.

    Returns:
        The equivalent Anthropic messages.
    """
    turns: list[MessageParam] = []
    for message in messages:
        match message.role:
            case "user":
                turns.append({"role": "user", "content": message.content})
            case "assistant":
                turns.append({"role": "assistant", "content": _assistant_blocks(message)})
            case "tool":
                result: ToolResultBlockParam = {
                    "type": "tool_result",
                    "tool_use_id": message.call_id or "",
                    "content": message.content,
                }
                if turns and turns[-1]["role"] == "user" and isinstance(turns[-1]["content"], list):
                    turns[-1]["content"].append(result)
                else:
                    turns.append({"role": "user", "content": [result]})
    return turns


def _assistant_blocks(message: Message) -> list[TextBlockParam | ToolUseBlockParam]:
    """Build the content blocks of an assistant turn: its text, then its tool calls.

    Args:
        message: A shared assistant message.

    Returns:
        The Anthropic content blocks.
    """
    blocks: list[TextBlockParam | ToolUseBlockParam] = []
    if message.content:
        blocks.append({"type": "text", "text": message.content})
    for call in message.skill_calls:
        blocks.append({"type": "tool_use", "id": call.id, "name": call.name, "input": call.args})
    return blocks


def _to_anthropic_tool(tool: SkillSpec) -> ToolParam:
    """Translate a shared skill spec into an Anthropic tool definition.

    Args:
        tool: The shared skill spec.

    Returns:
        The equivalent Anthropic tool.
    """
    return {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
