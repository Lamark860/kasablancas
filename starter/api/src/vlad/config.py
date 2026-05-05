"""Конфигурация через переменные окружения."""
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/local.db"
    swe_ephe_path: str = "./ephe"
    cors_origins: list[str] = ["http://localhost:3100"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        # pydantic-settings по умолчанию хочет JSON для list-полей.
        # Принимаем и CSV ("a,b,c"), чтобы .env читался по-человечески.
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @property
    def ephe_path_abs(self) -> Path:
        return Path(self.swe_ephe_path).resolve()


settings = Settings()
