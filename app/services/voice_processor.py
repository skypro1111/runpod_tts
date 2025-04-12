import os
import pickle
from pathlib import Path
from typing import Any
import aioredis
import asyncio
from sqlmodel import Session, select
import logging

from app.models.voice import Voice, VoiceStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        self.redis = None
        self.cache_dir = Path(settings.VOICE_CACHE_DIR)
        self.upload_dir = Path(settings.VOICE_UPLOAD_DIR)
        
        # Ensure directories exist
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)

    async def init_redis(self):
        """Initialize Redis connection."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False  # We need bytes for pickle data
            )
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def process_voice(self, voice: Voice, session: Session) -> None:
        """
        Process voice file and create cache.
        
        Args:
            voice: Voice model instance
            session: Database session
        """
        try:
            # Update status to processing
            voice.status = VoiceStatus.PROCESSING
            session.add(voice)
            session.commit()
            
            # Mock processing - use configured cache directory
            example_cache = self.cache_dir / "example.pkl"
            voice.cache_file_path = str(example_cache)
            
            # Update voice status
            voice.status = VoiceStatus.READY
            session.add(voice)
            session.commit()
            
            # Cache in Redis
            await self.cache_voice(voice)
            
        except Exception as e:
            logger.error(f"Error processing voice {voice.id}: {e}")
            voice.status = VoiceStatus.FAILED
            session.add(voice)
            session.commit()
            raise

    async def cache_voice(self, voice: Voice) -> None:
        """
        Cache voice data in Redis.
        
        Args:
            voice: Voice model instance
        """
        await self.init_redis()
        
        # Mock cache data
        cache_data = {
            "voice_id": voice.id,
            "cache_path": voice.cache_file_path,
            "processed_data": b"mock_processed_data"  # This would be real processed data
        }
        
        # Cache in Redis
        await self.redis.set(
            voice.cache_key,
            pickle.dumps(cache_data),
            ex=settings.VOICE_CACHE_TTL  # Cache TTL in seconds
        )

    async def get_cached_voice(self, voice_id: int) -> Any:
        """
        Get cached voice data from Redis.
        
        Args:
            voice_id: Voice ID
            
        Returns:
            Cached voice data or None if not found
        """
        await self.init_redis()
        
        cache_key = f"voice:{voice_id}:cache"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return pickle.loads(cached)
        return None

    async def load_all_voices_to_cache(self, session: Session) -> None:
        """
        Load all processed voices to Redis cache.
        
        Args:
            session: Database session
        """
        voices = session.exec(
            select(Voice).where(Voice.status == VoiceStatus.READY)
        ).all()
        
        for voice in voices:
            await self.cache_voice(voice)
            logger.info(f"Cached voice {voice.id} in Redis")

    def process_voice_data(self, voice_id: str, voice_data: bytes) -> dict:
        """Process voice data and cache the results"""
        # Save uploaded voice data
        voice_file = self.upload_dir / f"{voice_id}.wav"
        with open(voice_file, "wb") as f:
            f.write(voice_data)
            
        # Process voice (placeholder for actual processing)
        processed_data = {
            "voice_id": voice_id,
            "parameters": {
                "pitch": 1.0,
                "speed": 1.0,
                # Add other voice parameters
            }
        }
        
        # Cache processed results
        cache_file = self.cache_dir / f"{voice_id}.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump(processed_data, f)
            
        return processed_data
        
    def get_cached_voice_data(self, voice_id: str) -> dict | None:
        """Retrieve cached voice processing results"""
        cache_file = self.cache_dir / f"{voice_id}.pkl"
        if not cache_file.exists():
            return None
            
        with open(cache_file, "rb") as f:
            return pickle.load(f)
            
    def delete_voice_data(self, voice_id: str) -> bool:
        """Delete voice data and cache"""
        voice_file = self.upload_dir / f"{voice_id}.wav"
        cache_file = self.cache_dir / f"{voice_id}.pkl"
        
        success = True
        if voice_file.exists():
            try:
                voice_file.unlink()
            except Exception:
                success = False
                
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                success = False
                
        return success

# Global instance
voice_processor = VoiceProcessor() 