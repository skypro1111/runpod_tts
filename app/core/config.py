from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, AnyHttpUrl, field_validator
import secrets
from typing import Any

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TTS Service API"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    SQLITE_URL: str = "sqlite:///./sql_app.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    VOICE_CACHE_TTL: int = 60 * 60 * 24  # 24 hours
    
    # Voice Processing
    MEDIA_ROOT: str = "/media"
    VOICE_UPLOAD_DIR: str = "/media/voices/uploads"
    VOICE_CACHE_DIR: str = "/media/voices/cache"
    MAX_VOICE_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_VOICE_TYPES: List[str] = ["audio/wav", "audio/x-wav"]
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("CORS_ORIGINS", mode='before')
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # First superuser
    FIRST_SUPERUSER: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin"

    # RunPod
    RUNPOD_API_KEY: str
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding='utf-8',
        extra='allow'  # Allow extra fields from env file
    )

settings = Settings() 