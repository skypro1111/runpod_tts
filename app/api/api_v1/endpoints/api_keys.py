from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlmodel import Session, select
from datetime import datetime

from app.core.security import generate_api_key, get_api_key_prefix, hash_api_key
from app.db.init_db import get_session
from app.models.api_key import APIKey, APIKeyCreate, APIKeyResponse, APIKeyCreateResponse
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    *,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    api_key_in: APIKeyCreate,
) -> APIKeyCreateResponse:
    """
    Create a new API key for the current user.
    
    Args:
        api_key_in: API key creation data including name and optional expiration.
        
    Returns:
        Created API key data including the key (shown only once).
    """
    api_key_raw, hashed_key = generate_api_key()
    
    api_key = APIKey(
        **api_key_in.model_dump(),
        key=hashed_key,
        user_id=current_user.id
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    # Create response without the hashed key
    response_data = api_key.model_dump()
    response_data.pop('key')  # Remove hashed key
    
    return APIKeyCreateResponse(
        **response_data,
        key=api_key_raw,  # Add the raw key
        prefix=get_api_key_prefix(api_key_raw)
    )

@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
) -> List[APIKeyResponse]:
    """
    List all API keys for the current user.
    
    Returns:
        List of API keys without the actual key values.
    """
    api_keys = session.exec(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    ).all()
    
    return [
        APIKeyResponse(
            **key.model_dump(exclude={'key'}),  # Exclude the hashed key
            prefix=key.key[:8]  # Use first 8 chars of hash as prefix
        )
        for key in api_keys
    ]

@router.get("/check/{api_key}")
async def check_api_key(
    api_key: str,
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    """Debug endpoint to check API key status."""
    hashed_key = hash_api_key(api_key)
    db_api_key = session.exec(
        select(APIKey).where(APIKey.key == hashed_key)
    ).first()
    
    if not db_api_key:
        return {
            "status": "not_found",
            "message": "API key not found in database",
            "hashed_key_prefix": hashed_key[:8]
        }
    
    user = session.get(User, db_api_key.user_id)
    return {
        "status": "found",
        "is_active": db_api_key.is_active,
        "expires_at": db_api_key.expires_at,
        "user_email": user.email if user else None,
        "user_active": user.is_active if user else None,
        "hashed_key_prefix": hashed_key[:8],
        "stored_key_prefix": db_api_key.key[:8]
    }

@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete an API key.
    
    Args:
        api_key_id: ID of the API key to delete.
    """
    api_key = session.get(APIKey, api_key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    session.delete(api_key)
    session.commit() 