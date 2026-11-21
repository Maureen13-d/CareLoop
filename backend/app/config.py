from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CARELOOP_", extra="ignore")
    cors_origins: list[str] = ["http://localhost:3000"]
    seed_cases: int = 25
    seed: int = 42
    demo_scenario: bool = False
    # Anchored to backend/ so the same database is used wherever uvicorn is launched from.
    database_url: str = f"sqlite:///{BACKEND_DIR / 'careloop.db'}"


settings = Settings()
