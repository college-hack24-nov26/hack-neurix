from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List

_DEFAULT_SECRET = "homecare-super-secret-key-change-in-production-min-32chars"


def is_real_key(value: str) -> bool:
    """
    True only for something that looks like a real API key.

    Empty strings and copy-pasted placeholders ("your_key_here", "sk-xxxx",
    "<paste key>") are treated as "not configured" so the app reports the
    truth instead of trying a provider that can never succeed.
    """
    v = (value or "").strip()
    if len(v) < 20:
        return False
    low = v.lower()
    return not any(t in low for t in ("your_", "your-", "xxxx", "changeme", "paste", "example", "<", ">"))


class Settings(BaseSettings):
    # ── Application Settings ─────────────────────────────────────
    APP_NAME: str = "HomeCare+"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Database Settings (PostgreSQL) ───────────────────────────
    # Any standard Postgres URL works (postgres://, postgresql://,
    # postgresql+asyncpg://) — it is normalised to the asyncpg driver below.
    DATABASE_URL: str = "postgresql+asyncpg://homecare:homecare@localhost:5432/homecare_plus"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800      # seconds
    DB_ECHO: bool = False            # set True to log every SQL statement

    # ── JWT Authentication ───────────────────────────────────────
    SECRET_KEY: str = _DEFAULT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── CORS Configuration ───────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://homecare.plus",
    ]

    # ── File Upload Settings ─────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 20

    # ── AI / LLM API Keys (Optional) ─────────────────────────────
    # GROQ_API_KEY: primary chat model (fast + free tier available)
    # ANTHROPIC_API_KEY: used for vision (image / report analysis) + chat fallback
    # OPENAI_API_KEY: final fallback for chat + vision
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # ── AI Model Configuration ───────────────────────────────────
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"
    ANTHROPIC_VISION_MODEL: str = "claude-sonnet-5-5"
    # Tried automatically if the primary Anthropic model name is not available to the key.
    ANTHROPIC_FALLBACK_MODEL: str = "claude-sonnet-4-5-20250929"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_VISION_MODEL: str = "gpt-4o"
    # Groq vision model (free tier available). Groq retires models from time to time:
    # if one stops working, see https://console.groq.com/docs/vision and change it here / in .env.
    GROQ_VISION_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_VISION_FALLBACK_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    AI_REQUEST_TIMEOUT: int = 30  # seconds (text chat)

    # ── Image / report analysis ──────────────────────────────────
    # Comma-separated, first available wins; the rest are automatic fallbacks.
    VISION_PROVIDER_ORDER: str = "anthropic,openai,groq"
    TEXT_PROVIDER_ORDER: str = "groq,anthropic,openai"
    AI_VISION_TIMEOUT: int = 90        # seconds per provider call (vision models are slower)
    VISION_MAX_EDGE: int = 1568        # longest image side sent to the model (px)
    VISION_MIN_EDGE: int = 128         # smaller images are rejected as unreadable

    # ── Google Maps API ──────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalise_database_url(cls, v: str) -> str:
        """Accept postgres:// and postgresql:// (Heroku/Render/Supabase style)."""
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix):]
        if v.startswith("postgresql+psycopg2://"):
            return "postgresql+asyncpg://" + v[len("postgresql+psycopg2://"):]
        return v

    def model_post_init(self, __context) -> None:
        if self.APP_ENV.lower() == "production" and self.SECRET_KEY == _DEFAULT_SECRET:
            raise ValueError(
                "SECRET_KEY must be changed from its default value when APP_ENV=production."
            )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"      # old MONGO_* variables in a legacy .env are simply ignored


# Global settings instance
settings = Settings()
