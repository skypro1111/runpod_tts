from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, api_keys, tts, voices

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(tts.router, prefix="/tts", tags=["tts"])
api_router.include_router(voices.router, prefix="/voices", tags=["voices"]) 