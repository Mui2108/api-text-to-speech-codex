from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.realtime_transcription_router import router as realtime_transcription_router
from app.routers.transcription_router import router as transcription_router
from app.schemas import HealthResponse
from app.services.realtime_transcription_service import RealtimeTranscriptionService
from app.services.whisper_service import WhisperService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    app.state.whisper_service = WhisperService(
        api_key=settings.elevenlabs_api_key,
        model_id=settings.elevenlabs_model_id,
    )
    app.state.realtime_transcription_service = RealtimeTranscriptionService()
    yield


app = FastAPI(title="elevenlabs-speech-to-text-api", lifespan=lifespan)
settings = get_settings()

origins = settings.cors_origins_list
if origins == ["*"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="elevenlabs-speech-to-text-api")


app.include_router(transcription_router)
app.include_router(realtime_transcription_router)
