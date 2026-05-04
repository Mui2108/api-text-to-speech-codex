from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status

from app.config import Settings, get_settings
from app.schemas import MeetingChunksResponse, MeetingJobResponse
from app.services.meeting_transcription_service import MeetingTranscriptionService
from app.utils.file_utils import save_upload_file, validate_file_size, validate_video_upload

router = APIRouter(prefix="/api/meeting-transcriptions", tags=["meeting-transcriptions"])


def get_meeting_transcription_service(request: Request) -> MeetingTranscriptionService:
    return request.app.state.meeting_transcription_service


@router.post("", response_model=MeetingJobResponse)
async def create_meeting_transcription(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    service: MeetingTranscriptionService = Depends(get_meeting_transcription_service),
) -> MeetingJobResponse:
    """Create a meeting transcription job and process it in the background."""
    await validate_file_size(file, settings.max_upload_size_mb)
    validate_video_upload(file.filename or "", file.content_type)

    saved_path = await save_upload_file(file, settings.upload_dir)
    job = service.create_job(file_path=saved_path, file_name=file.filename or "uploaded-video")
    background_tasks.add_task(service.process_job, job["job_id"])
    return MeetingJobResponse(**job)


@router.get("/{job_id}", response_model=MeetingJobResponse)
async def get_meeting_transcription_job(
    job_id: str,
    service: MeetingTranscriptionService = Depends(get_meeting_transcription_service),
) -> MeetingJobResponse:
    """Get current status and chunk progress for a meeting transcription job."""
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return MeetingJobResponse(**job)


@router.get("/{job_id}/chunks", response_model=MeetingChunksResponse)
async def get_meeting_transcription_chunks(
    job_id: str,
    service: MeetingTranscriptionService = Depends(get_meeting_transcription_service),
) -> MeetingChunksResponse:
    """Get only chunk-level statuses and transcripts for a job."""
    chunks = service.get_chunks(job_id)
    if chunks is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return MeetingChunksResponse(job_id=job_id, chunks=chunks)
