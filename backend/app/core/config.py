from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Jal-Drishti API"
    environment: str = "development"
    database_url: str = "sqlite:///./jal_drishti.db"
    jwt_secret: str = "change-me-in-production"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    risk_block_threshold: float = 0.75
    max_risk_age_minutes: int = 90
    model_version: str = "baseline-v1"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [v.strip() for v in self.cors_origins.split(",") if v.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
