import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://user:pass@localhost:5432/rustbucket?sslmode=require"
    REDIS_URL: str = "redis://localhost:6379/0"
    GITHUB_TOKEN: str = ""
    SCANNER_MODE: str = "stub"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8080"

    class Config:
        env_file = ".env"

settings = Settings()