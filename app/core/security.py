from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
import secrets
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its hash.
    
    Returns:
        Tuple containing (api_key, hashed_key)
    """
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    hashed_key = hash_api_key(api_key)
    return api_key, hashed_key

def hash_api_key(api_key: str) -> str:
    """Hash an API key.
    
    Args:
        api_key: The API key to hash
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

def get_api_key_prefix(api_key: str) -> str:
    """Get the prefix of an API key for display purposes.
    
    Args:
        api_key: The API key
        
    Returns:
        First 8 characters of the API key
    """
    return api_key[:8] 