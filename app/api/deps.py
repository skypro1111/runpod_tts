from typing import Annotated, Optional
from datetime import datetime
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError
from sqlmodel import Session, select
import logging

from app.core.config import settings
from app.core.security import hash_api_key
from app.db.init_db import get_session
from app.models.user import User, TokenPayload
from app.models.api_key import APIKey

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Optional[User]:
    """
    Get current user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        Current user or None if token is invalid or user not found
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            return None
    except JWTError:
        return None
        
    user = session.get(User, token_data.sub)
    if not user or not user.is_active:
        return None

    return user

async def get_current_user_from_api_key(
    session: Annotated[Session, Depends(get_session)],
    api_key: Annotated[str, Depends(api_key_header)],
) -> Optional[User]:
    """
    Get current user from API key.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        Current user or None if API key is invalid or expired
    """
    if not api_key:
        return None

    logger.info(f"Received API key: {api_key[:8]}...")  # Log only prefix for security
    hashed_key = hash_api_key(api_key)
    logger.info(f"Hashed key: {hashed_key[:8]}...")  # Log only prefix for security

    db_api_key = session.exec(
        select(APIKey).where(APIKey.key == hashed_key)
    ).first()
    
    if not db_api_key:
        logger.warning("API key not found in database")
        return None

    if not db_api_key.is_active:
        logger.warning("API key is inactive")
        return None

    if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
        logger.warning("API key has expired")
        return None

    # Update last used timestamp
    db_api_key.last_used_at = datetime.utcnow()
    session.add(db_api_key)
    session.commit()

    user = session.get(User, db_api_key.user_id)
    if not user or not user.is_active:
        logger.warning("User not found or inactive")
        return None

    logger.info(f"Successfully authenticated user: {user.email}")
    return user

async def get_current_user_with_api_key(
    user_from_token: Annotated[Optional[User], Depends(get_current_user)],
    user_from_api_key: Annotated[Optional[User], Depends(get_current_user_from_api_key)],
) -> User:
    """
    Get current user from either JWT token or API key.
    
    Returns:
        Current user
        
    Raises:
        HTTPException: If neither authentication method is valid
    """
    if user_from_token:
        return user_from_token
    if user_from_api_key:
        return user_from_api_key
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    ) 