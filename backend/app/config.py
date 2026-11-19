from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CARELOOP_")

    cors_origins: list[str] = ["http://localhost:3000"]
    seed_cases: int = 25
    seed: int = 42


settings = Settings()
