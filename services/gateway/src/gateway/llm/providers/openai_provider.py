"""Adapter for providers speaking the OpenAI chat completions API."""

import json

import openai
from core.models.chat import Completion, Message, SkillCall, SkillSpec
from core.tracing import traced
from mlflow.entities import SpanType
from openai.types.chat import (
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

from gateway.llm.providers.provider import ProviderError

# STUB: Ollama ignores the key; a real OpenAI endpoint needs one from settings.
API_KEY = "unused"


class OpenAIProvider:
    """Calls an OpenAI-compatible endpoint and translates to and from the shared chat models."""

    def __init__(self, name: str, base_url: str) -> None:
        """Create the adapter.

        Args:
            name: Provider name reported in completions.
            base_url: Endpoint of the OpenAI-compatible API.
        """
        self.name = name
        self.client = openai.AsyncOpenAI(base_url=base_url, api_key=API_KEY)

    @traced("openai_provider", SpanType.LLM)
    async def complete(self, model: str, messages: list[Message], tools: list[SkillSpec]) -> Completion:
        """Complete a conversation through the OpenAI API.

        Args:
            model: Provider-side model name.
            messages: The conversation so far.
            tools: Skills the model may call.

        Returns:
            The model's text and/or skill calls.

        Raises:
            ProviderError: If the endpoint fails or is unreachable.
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[_to_openai_message(message) for message in messages],
                tools=[_to_openai_tool(tool) for tool in tools],
                temperature=0,
            )
        except openai.OpenAIError as error:
            raise ProviderError(f"{self.name}: {error}") from error
        reply = response.choices[0].message
        calls = [
            SkillCall(id=call.id, name=call.function.name, args=json.loads(call.function.arguments))
            for call in reply.tool_calls or []
            if call.type == "function"
        ]
        return Completion(model=model, provider=self.name, text=reply.content or None, skill_calls=calls)


def _to_openai_message(message: Message) -> ChatCompletionMessageParam:
    """Translate a shared message into the OpenAI format.

    Args:
        message: The shared message.

    Returns:
        The equivalent OpenAI message.
    """
    match message.role:
        case "system":
            return {"role": "system", "content": message.content}
        case "user":
            return {"role": "user", "content": message.content}
        case "tool":
            return {"role": "tool", "content": message.content, "tool_call_id": message.call_id or ""}
        case "assistant":
            calls: list[ChatCompletionMessageFunctionToolCallParam] = [
                {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.args)}}
                for c in message.skill_calls
            ]
            if calls:
                return {"role": "assistant", "content": message.content, "tool_calls": calls}
            return {"role": "assistant", "content": message.content}


def _to_openai_tool(tool: SkillSpec) -> ChatCompletionToolParam:
    """Translate a shared skill spec into an OpenAI tool definition.

    Args:
        tool: The shared skill spec.

    Returns:
        The equivalent OpenAI tool.
    """
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description, "parameters": tool.input_schema},
    }
