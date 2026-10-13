"""Prompts read from the MLflow prompt registry (needs the core[tracing] extra)."""

import asyncio

import mlflow
from core.models.prompts import Prompt


class MlflowPromptStore:
    """Loads prompts from the registry of the MLflow server set up by core.tracing.setup."""

    async def load(self, name: str, ref: str) -> Prompt:
        """Load one prompt version; inside a trace, MLflow links the version to it.

        Args:
            name: Registered prompt name.
            ref: A version number, or an alias (cached by MLflow for 60 s by default).

        Returns:
            The prompt text, with the version's commit message as its description.

        Raises:
            TypeError: The version is a chat prompt (a list of messages), not a text prompt.
        """
        uri = f"prompts:/{name}/{ref}" if ref.isdigit() else f"prompts:/{name}@{ref}"
        version = await asyncio.to_thread(mlflow.genai.load_prompt, uri)  # the client is blocking
        if not isinstance(version.template, str):
            raise TypeError(f"{uri} is a chat prompt; only text prompts are supported")
        return Prompt(name=name, version=version.version, description=version.commit_message or "",
                      text=version.template)
