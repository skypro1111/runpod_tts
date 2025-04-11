from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict
from app.models.user import User

class APIKeyBase(SQLModel):
    """Base API key model with common attributes."""
    name: str = Field(index=True, description="Name/description of the API key")
    is_active: bool = Field(default=True, description="Whether the API key is active")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration date of the API key")

    model_config = ConfigDict(from_attributes=True)

class APIKey(APIKeyBase, table=True):
    """Database API key model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True, description="Hashed API key")
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, description="API key creation timestamp")
    last_used_at: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    
    # Relationship
    user: User = Relationship(back_populates="api_keys")

class APIKeyCreate(APIKeyBase):
    """API key creation model."""
    pass

class APIKeyResponse(APIKeyBase):
    """API key response model."""
    id: int
    created_at: datetime
    last_used_at: Optional[datetime]
    prefix: str = Field(description="First few characters of the API key")

class APIKeyCreateResponse(APIKeyResponse):
    """API key creation response including the full key."""
    key: str = Field(description="Full API key (only shown once at creation)") 