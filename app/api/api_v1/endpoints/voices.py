from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime
import shutil
import os
from pathlib import Path

from app.core.config import settings
from app.db.init_db import get_session
from app.models.voice import Voice, VoiceCreate, VoiceResponse, VoiceStatus
from app.models.user import User
from app.api.deps import get_current_user_with_api_key
from app.services.voice_processor import voice_processor

router = APIRouter()

@router.post("/", response_model=VoiceResponse)
async def create_voice(
    *,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user_with_api_key)],
    voice_data: VoiceCreate,
    audio_file: UploadFile = File(...),
) -> VoiceResponse:
    """
    Create a new voice.
    
    Args:
        voice_data: Voice metadata
        audio_file: Voice audio file (WAV format)
    """
    # Validate file type
    if audio_file.content_type not in settings.ALLOWED_VOICE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {audio_file.content_type} not allowed. Must be WAV."
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.VOICE_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{current_user.id}_{timestamp}_{audio_file.filename}"
    file_path = upload_dir / filename
    
    # Save uploaded file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
    finally:
        audio_file.file.close()
    
    # Create voice record
    voice = Voice(
        **voice_data.model_dump(),
        user_id=current_user.id,
        original_file_path=str(file_path)
    )
    session.add(voice)
    session.commit()
    session.refresh(voice)
    
    # Process voice in background
    background_tasks.add_task(
        voice_processor.process_voice,
        voice=voice,
        session=session
    )
    
    return voice

@router.get("/", response_model=List[VoiceResponse])
async def list_voices(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user_with_api_key)],
    skip: int = 0,
    limit: int = 100,
) -> List[VoiceResponse]:
    """
    List all voices for the current user.
    """
    voices = session.exec(
        select(Voice)
        .where(Voice.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return voices

@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user_with_api_key)],
) -> VoiceResponse:
    """
    Get voice details.
    """
    voice = session.get(Voice, voice_id)
    if not voice or voice.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )
    return voice

@router.delete("/{voice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice(
    voice_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user_with_api_key)],
) -> None:
    """
    Delete a voice.
    """
    voice = session.get(Voice, voice_id)
    if not voice or voice.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )
    
    # Delete files
    if voice.original_file_path and os.path.exists(voice.original_file_path):
        os.remove(voice.original_file_path)
    if voice.cache_file_path and os.path.exists(voice.cache_file_path):
        os.remove(voice.cache_file_path)
    
    # Delete from database
    session.delete(voice)
    session.commit() 