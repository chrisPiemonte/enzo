"""Eval settings loaded from env / the root .env (prefix EVALS_)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the eval harness."""

    model_config = SettingsConfigDict(env_prefix="EVALS_", env_file=".env", extra="ignore")

    dir: Path = Path("data/context/evals")
    mlflow_url: str = "http://localhost:5001"
    experiment: str = "evals"


settings = Settings()
