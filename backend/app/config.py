from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    youtube_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    typesafe_api_key: str = ""
    typesafe_default_model: str = "jev-1.13.0"
    jev_concurrency: int = 8
    classify_models: str = "openai/gpt-oss-20b,openai/gpt-oss-120b"
    max_comments: int = 1000
    max_comment_chars: int = 1000
    cors_origins: str = "http://localhost:3000"
    cache_ttl_seconds: int = 600

    @property
    def classify_model_list(self) -> list[str]:
        return [m.strip() for m in self.classify_models.split(",") if m.strip()]

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
