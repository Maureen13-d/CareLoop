"""Application settings, read from environment variables or backend/.env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), extra="ignore")

    database_url: str = f"sqlite:///{BACKEND_DIR / 'careloop.db'}"
    secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 480
    enable_scheduler: bool = False
    scheduler_interval_seconds: int = 60
    require_consent_for_tracking: bool = True
    cors_origins: str = "http://localhost:3000"
    pathways_dir: str = str(REPO_ROOT / "pathways")
    demo_password: str = "careloop-demo"


settings = Settings()
