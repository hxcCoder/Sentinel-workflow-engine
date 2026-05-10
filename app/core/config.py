from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )

    app_name: str = "SentinelLab"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = Field(..., validation_alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", validation_alias="REDIS_URL")

    secret_key: str = Field(..., validation_alias="SECRET_KEY")

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


settings = Settings()