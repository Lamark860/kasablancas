"""Конфигурация через переменные окружения."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    database_url: str = "sqlite:///./data/local.db"
    swe_ephe_path: str = "./ephe"
    cors_origins: list[str] = ["http://localhost:3000"]
    
    @property
    def ephe_path_abs(self) -> Path:
        return Path(self.swe_ephe_path).resolve()


settings = Settings()
