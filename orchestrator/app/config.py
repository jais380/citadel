"""All settings come from environment variables (.env via docker compose)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    citadel_secret: str = "change-me"
    pipeline_max_rounds: int = 3
    runs_dir: str = "/app/runs"

    omniroute_base_url: str = "http://omniroute:20128/v1"
    omniroute_api_key: str = ""
    model_brain: str = "citadel-brain"
    model_worker: str = "citadel-worker"
    model_cheap: str = "citadel-cheap"

    ollama_base_url: str = "http://host.docker.internal:11434/v1"
    model_private: str = "qwen2.5-coder:7b"
    model_embed: str = "nomic-embed-text"

    database_url: str = ""
    redis_url: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


@lru_cache
def settings() -> Settings:
    return Settings()
