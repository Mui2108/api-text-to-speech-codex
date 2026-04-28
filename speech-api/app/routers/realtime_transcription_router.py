from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas import (
    RealtimeChunkAckResponse,
    RealtimeChunkIngestRequest,
    RealtimeSessionCloseResponse,
    RealtimeSessionCreateRequest,
    RealtimeSessionResponse,
)
from app.services.realtime_transcription_service import RealtimeTranscriptionService

router = APIRouter(prefix="/api/realtime-transcriptions", tags=["realtime-transcriptions"])


def get_realtime_service(request: Request) -> RealtimeTranscriptionService:
    return request.app.state.realtime_transcription_service


@router.post("/sessions", response_model=RealtimeSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_realtime_session(
    payload: RealtimeSessionCreateRequest,
    realtime_service: RealtimeTranscriptionService = Depends(get_realtime_service),
) -> RealtimeSessionResponse:
    session = realtime_service.create_session(language=payload.language)
    return RealtimeSessionResponse(**session)


@router.get("/sessions/{session_id}", response_model=RealtimeSessionResponse)
async def get_realtime_session(
    session_id: str,
    realtime_service: RealtimeTranscriptionService = Depends(get_realtime_service),
) -> RealtimeSessionResponse:
    try:
        session = realtime_service.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RealtimeSessionResponse(**session)


@router.post("/sessions/{session_id}/chunks", response_model=RealtimeChunkAckResponse)
async def ingest_realtime_chunk(
    session_id: str,
    payload: RealtimeChunkIngestRequest,
    realtime_service: RealtimeTranscriptionService = Depends(get_realtime_service),
) -> RealtimeChunkAckResponse:
    try:
        ack = realtime_service.append_chunk(
            session_id=session_id,
            chunk_index=payload.chunk_index,
            duration_ms=payload.duration_ms,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RealtimeChunkAckResponse(**ack)


@router.post("/sessions/{session_id}/close", response_model=RealtimeSessionCloseResponse)
async def close_realtime_session(
    session_id: str,
    realtime_service: RealtimeTranscriptionService = Depends(get_realtime_service),
) -> RealtimeSessionCloseResponse:
    try:
        session = realtime_service.close_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RealtimeSessionCloseResponse(
        session_id=session["session_id"],
        status=session["status"],
        chunk_count=session["chunk_count"],
    )
