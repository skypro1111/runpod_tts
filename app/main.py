from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.init_db import create_db_and_tables, get_session
from app.services.voice_processor import voice_processor

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    await create_db_and_tables()
    
    # Load all voices to Redis cache
    async for session in get_session():
        await voice_processor.load_all_voices_to_cache(session)
        break
    
    yield
    
    # Shutdown
    await voice_processor.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    summary="Text-to-Speech Service API with authentication",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR) 