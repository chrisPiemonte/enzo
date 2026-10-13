"""Prompt sync settings loaded from env / the root .env (prefix PROMPTS_)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the prompt sync job."""

    model_config = SettingsConfigDict(env_prefix="PROMPTS_", env_file=".env", extra="ignore")

    dir: Path = Path("data/context/prompts")
    mlflow_url: str = "http://localhost:5001"


settings = Settings()
