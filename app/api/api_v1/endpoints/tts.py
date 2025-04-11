from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlmodel import Session
import os
from pathlib import Path

from app.api.deps import get_current_user_with_api_key
from app.models.user import User
from app.models.tts import TTSRequest, TTSResponse
from app.core.config import settings

router = APIRouter()

# For demo purposes, using a static example file
EXAMPLE_WAV = Path(__file__).parent.parent.parent.parent / "static" / "example.wav"

@router.post("/generate_speech", response_model=TTSResponse)
async def generate_speech(
    *,
    request: TTSRequest,
    current_user: Annotated[User, Depends(get_current_user_with_api_key)],
) -> TTSResponse | StreamingResponse:
    """
    Generate speech from text.
    
    Args:
        request: Text-to-Speech request containing text and voice settings
        
    Returns:
        Audio file or streaming response depending on the request
    """
    # Ensure example file exists
    if not EXAMPLE_WAV.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Example audio file not found"
        )
    
    if request.stream:
        # For streaming response
        def iterfile():
            with open(EXAMPLE_WAV, mode="rb") as file:
                yield from file
        
        return StreamingResponse(
            iterfile(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'attachment; filename="speech.wav"'
            }
        )
    else:
        # For file download
        return TTSResponse(
            audio_url=f"/api/v1/tts/download/{EXAMPLE_WAV.name}",
            duration=3.0,  # Placeholder duration
            text=request.text
        )

@router.get("/download/{filename}")
async def download_audio(
    filename: str,
    current_user: Annotated[User, Depends(get_current_user_with_api_key)],
) -> FileResponse:
    """
    Download generated audio file.
    
    Args:
        filename: Name of the audio file to download
        
    Returns:
        Audio file as attachment
    """
    if not EXAMPLE_WAV.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return FileResponse(
        EXAMPLE_WAV,
        media_type="audio/wav",
        filename="speech.wav"
    ) 