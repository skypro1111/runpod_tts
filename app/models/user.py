from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from pydantic import EmailStr, ConfigDict
from datetime import datetime

class UserBase(SQLModel):
    """Base user model with common attributes."""
    email: EmailStr = Field(unique=True, index=True)
    is_active: bool = Field(default=True, description="Whether the user is active")
    is_superuser: bool = Field(default=False, description="Whether the user has admin privileges")
    
    model_config = ConfigDict(from_attributes=True)

class User(UserBase, table=True):
    """Database user model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(description="Hashed password string")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="User creation timestamp")
    
    # Relationships
    api_keys: List["APIKey"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(description="Plain text password for user creation")

class UserUpdate(SQLModel):
    """User update model with optional fields."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserResponse(UserBase):
    """User response model without sensitive data."""
    id: int
    created_at: datetime

class Token(SQLModel):
    """Token response model."""
    access_token: str
    token_type: str

class TokenPayload(SQLModel):
    """Token payload model."""
    sub: Optional[int] = None 