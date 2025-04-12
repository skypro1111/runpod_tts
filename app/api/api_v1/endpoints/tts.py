from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from sqlmodel import Session
import os
from pathlib import Path
import uuid

from app.api.deps import get_current_user_with_api_key
from app.models.user import User
from app.models.tts import TTSRequest, TTSResponse
from app.core.config import settings

router = APIRouter()

# For actual TTS generation
def generate_tts_file(text: str, output_path: str):
    # TODO: Implement actual TTS generation here
    # For now, we'll just create an empty file
    with open(output_path, 'wb') as f:
        f.write(b'')  # Placeholder for actual TTS content

@router.post("/generate_speech")
async def generate_speech(text: str, background_tasks: BackgroundTasks, stream: bool = False):
    # Generate unique filename for this request
    filename = f"{uuid.uuid4()}.wav"
    output_path = os.path.join(settings.MEDIA_ROOT, "tts_output", filename)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate TTS file
    background_tasks.add_task(generate_tts_file, text, output_path)
    
    if stream:
        return StreamingResponse(
            open(output_path, mode="rb"),
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        return {"filename": filename}

@router.get("/download/{filename}")
async def download_audio(filename: str):
    file_path = os.path.join(settings.MEDIA_ROOT, "tts_output", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(
        file_path,
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    ) 