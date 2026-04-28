from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.config import Settings, get_settings
from app.schemas import TranscriptionResponse
from app.services.whisper_service import WhisperService
from app.utils.file_utils import delete_file_safely, save_upload_file, validate_file_size

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])


def get_whisper_service(request: Request) -> WhisperService:
    return request.app.state.whisper_service


@router.post("", response_model=TranscriptionResponse)
async def create_transcription(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    settings: Settings = Depends(get_settings),
    whisper_service: WhisperService = Depends(get_whisper_service),
) -> TranscriptionResponse:
    temp_file_path: str | None = None

    try:
        await validate_file_size(file, settings.max_upload_size_mb)
        temp_file_path = await save_upload_file(file, settings.upload_dir)
        result = whisper_service.transcribe(temp_file_path, language=language)
        return TranscriptionResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(exc)}",
        ) from exc
    finally:
        delete_file_safely(temp_file_path)
