"""
Centralized application configuration.

Loads all settings from environment variables (.env file). No secrets
are hard-coded here — see .env.example for the variables you must set.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy backend/.env.example to backend/.env and fill it in."
        )
    return value


class Settings:
    # Database
    DATABASE_HOST: str = _require("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = _require("DATABASE_NAME", "career_platform")
    DATABASE_USER: str = _require("DATABASE_USER")
    DATABASE_PASSWORD: str = _require("DATABASE_PASSWORD")
    # Neon (and most hosted Postgres) requires SSL. Use "require" in production,
    # "prefer" is fine for a local pgAdmin/Postgres install.
    DATABASE_SSLMODE: str = os.getenv("DATABASE_SSLMODE", "prefer")
    DATABASE_POOL_MAX: int = int(os.getenv("DATABASE_POOL_MAX", "8"))

    # Auth
    JWT_SECRET: str = _require("JWT_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # AI provider (OpenAI-compatible chat completions API — Groq, OpenAI, etc.)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "")

    # CORS
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",")
        if origin.strip()
    ]


settings = Settings()
