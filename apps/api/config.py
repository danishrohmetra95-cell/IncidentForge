from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    FEATHERLESS_API_KEY: str = ""
    FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"
    MODEL_TIMEOUT_SECONDS: float = 60.0
    DATABASE_URL: str = "postgresql+asyncpg://incidentforge:incidentforge@localhost:5432/incidentforge"
    REDIS_URL: str = "redis://localhost:6379/0"
    DEEP_MODEL: str = ""
    FAST_MODEL: str = ""
    SYNTHESIS_MODEL: str = ""
    DEMO_MODE: bool = True
    LOG_LEVEL: str = "info"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
