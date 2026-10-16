from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    youtube_api_key: str = ""
    typesafe_api_key: str = ""
    typesafe_default_model: str = "jev-1.13.0"
    max_comments: int = 1000
    jev_concurrency: int = 16
    max_comment_chars: int = 1000
    cors_origins: str = "http://localhost:3000"
    cache_ttl_seconds: int = 600

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
