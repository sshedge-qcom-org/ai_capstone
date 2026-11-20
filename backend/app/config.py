from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    app_name: str = "AI Procurement Platform"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = f"sqlite:///{ROOT / 'procurement.db'}"
    jwt_secret: SecretStr = Field(min_length=32)
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=7, ge=1, le=30)
    cors_origins: list[str] = ["http://localhost:5173"]
    cookie_secure: bool = False

    @model_validator(mode="after")
    def production_security(self):
        if self.environment == "production" and (
            not self.cookie_secure
            or any(not origin.startswith("https://") for origin in self.cors_origins)
            or "*" in self.cors_origins
        ):
            raise ValueError("Production requires secure cookies and explicit HTTPS CORS origins")
        return self


settings = Settings()
