from typing import Optional
from pydantic import BaseModel, Field

class TTSRequest(BaseModel):
    """Text-to-Speech request model."""
    text: str = Field(..., description="Text to convert to speech")
    voice_id: int = Field(default=1, description="Voice ID to use for synthesis")
    stream: bool = Field(default=False, description="Whether to stream the audio response")

class TTSResponse(BaseModel):
    """Text-to-Speech response model for non-streaming responses."""
    audio_url: str = Field(..., description="URL to download the generated audio file")
    duration: float = Field(..., description="Duration of the audio in seconds")
    text: str = Field(..., description="Text that was converted to speech") 