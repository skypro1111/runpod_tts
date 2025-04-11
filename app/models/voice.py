from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict
from enum import Enum

class VoiceStatus(str, Enum):
    """Voice processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class Language(str, Enum):
    """Supported languages."""
    EN = "en"
    UK = "uk"
    RU = "ru"

class VoiceBase(SQLModel):
    """Base voice model with common attributes."""
    name: str = Field(index=True, description="Name of the voice")
    language: Language = Field(description="Language of the voice")
    description: Optional[str] = Field(default=None, description="Voice description")
    
    model_config = ConfigDict(from_attributes=True)

class Voice(VoiceBase, table=True):
    """Database voice model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    status: VoiceStatus = Field(default=VoiceStatus.PENDING, description="Processing status")
    original_file_path: str = Field(description="Path to the original audio file")
    sample_text: str = Field(description="Text used in the sample audio")
    cache_file_path: Optional[str] = Field(default=None, description="Path to the processed cache file")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Voice creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Redis cache key format: voice:{voice_id}:cache
    @property
    def cache_key(self) -> str:
        """Get Redis cache key for this voice."""
        return f"voice:{self.id}:cache"

class VoiceCreate(VoiceBase):
    """Voice creation model."""
    sample_text: str = Field(description="Text used in the sample audio")

class VoiceResponse(VoiceBase):
    """Voice response model."""
    id: int
    status: VoiceStatus
    created_at: datetime
    updated_at: datetime 