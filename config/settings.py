"""
Application settings loaded from environment variables / .env file.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is two levels up from this file (config/settings.py → root)
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Ensure runtime directories exist before settings are consumed
for _dir in ("data", "decision_models", "logs"):
    (BASE_DIR / _dir).mkdir(parents=True, exist_ok=True)

_DEFAULT_DB_URL = f"sqlite:///{(BASE_DIR / 'data' / 'rule_engine.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = _DEFAULT_DB_URL
    APP_NAME: str = "Invoice Rule Engine"
    LOG_LEVEL: str = "INFO"
    DEFAULT_ACTION: str = "SEND_TO_HUMAN_QUEUE"


settings = Settings()

# Convenience path constants
DECISION_MODELS_DIR: Path = BASE_DIR / "decision_models"
LOGS_DIR: Path = BASE_DIR / "logs"
DATA_DIR: Path = BASE_DIR / "data"
