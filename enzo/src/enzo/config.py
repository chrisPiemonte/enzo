"""Agent settings loaded from env / the root .env (prefix AGENT_)."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the local agent."""

    model_config = SettingsConfigDict(env_prefix="AGENT_", env_file=".env", extra="ignore")

    user: str = "user:maria"
    id: str = "agent:triage"
    model_alias: str = "triage-default"
    gateway_url: str = "http://localhost:8000"
    prompt: str = "triage-system"
    prompt_version: str = "production"
    prompts_dir: Path = Path("data/context/prompts")
    identity_file: Path = Path("data/context/identity.yaml")
    identity_secret: str = Field(validation_alias="IDENTITY_SECRET")  # shared by every service
    mlflow_url: str = "http://localhost:5001"
    experiment: str = "enzo"

    # Adapter switches, one per port.
    gateway: Literal["mock", "http"] = "mock"
    audit: Literal["mock"] = "mock"
    prompts: Literal["file", "mlflow"] = "file"


settings = Settings()
