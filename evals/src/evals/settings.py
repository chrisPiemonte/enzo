"""Eval settings loaded from env / the root .env (prefix EVALS_)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the eval harness."""

    model_config = SettingsConfigDict(env_prefix="EVALS_", env_file=".env", extra="ignore")

    dir: Path = Path("data/context/evals")
    mlflow_url: str = "http://localhost:5001"
    experiment: str = "evals"
    gateway_url: str = "http://localhost:8000"
    judge_alias: str = "judge"
    router_alias: str = "triage-default"  # the skills eval routes with the agent's own model
    judge_user: str = "user:evals"
    judge_agent: str = "agent:judge"


settings = Settings()
