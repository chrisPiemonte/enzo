"""Gateway settings loaded from env / the root .env (prefix GATEWAY_)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the model gateway."""

    model_config = SettingsConfigDict(env_prefix="GATEWAY_", env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    config: Path = Path("services/gateway/gateway.yaml")
    openai_url: str = "http://localhost:11434/v1"
    anthropic_url: str = "http://localhost:11434"
    docker_socket: str = "/var/run/docker.sock"
    mlflow_url: str = "http://localhost:5001"
    experiment: str = "gateway"


settings = Settings()
