"""Providers and model aliases, loaded from gateway.yaml."""

from pathlib import Path
from string import Template
from typing import Literal

import yaml
from pydantic import BaseModel, model_validator

ProviderKind = Literal["openai", "anthropic", "mock"]


class ProviderConfig(BaseModel):
    """Where a provider lives and which API format it speaks."""

    kind: ProviderKind
    base_url: str


class AliasConfig(BaseModel):
    """The provider and model behind a model alias."""

    provider: str
    model: str


class GatewayConfig(BaseModel):
    """All providers and aliases known to the gateway."""

    providers: dict[str, ProviderConfig]
    aliases: dict[str, AliasConfig]

    @model_validator(mode="after")
    def _aliases_use_known_providers(self) -> "GatewayConfig":
        """Reject aliases that point to a provider not declared in the config.

        Returns:
            The validated config.

        Raises:
            ValueError: If an alias names an unknown provider.
        """
        for name, alias in self.aliases.items():
            if alias.provider not in self.providers:
                raise ValueError(f"alias {name!r} uses unknown provider {alias.provider!r}")
        return self


def load_config(path: Path, variables: dict[str, str]) -> GatewayConfig:
    """Read the YAML config, replacing each ${name} with its variable.

    Args:
        path: Path to gateway.yaml.
        variables: Values for the ${name} placeholders.

    Returns:
        The validated gateway config.
    """
    text = Template(path.read_text()).substitute(variables)
    return GatewayConfig.model_validate(yaml.safe_load(text))
