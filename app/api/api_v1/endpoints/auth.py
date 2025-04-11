from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import Session
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.db.init_db import get_session
from app.models.user import User, UserCreate, Token, UserResponse
from app.core.security import get_password_hash

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token")

@router.post("/login/access-token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_access_token(
    session: Annotated[Session, Depends(get_session)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        form_data: OAuth2 password request form containing username and password.
        
    Returns:
        Token object containing access token and token type.
        
    Raises:
        HTTPException: If authentication fails or user is inactive.
    """
    user = session.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        token_type="bearer"
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    session: Annotated[Session, Depends(get_session)],
    user_in: UserCreate,
) -> UserResponse:
    """
    Create new user.
    
    Args:
        user_in: User creation data including email and password.
        
    Returns:
        Created user data without sensitive information.
        
    Raises:
        HTTPException: If user with provided email already exists.
    """
    user = session.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse.model_validate(user) 