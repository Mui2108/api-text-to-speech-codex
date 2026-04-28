from datetime import datetime

from pydantic import BaseModel


class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionResponse(BaseModel):
    text: str
    language: str | None
    duration: float | None
    segments: list[TranscriptionSegment]


class RealtimeSessionCreateRequest(BaseModel):
    language: str | None = None


class RealtimeChunkIngestRequest(BaseModel):
    chunk_index: int
    duration_ms: int | None = None


class RealtimeSessionResponse(BaseModel):
    session_id: str
    status: str
    language: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class RealtimeChunkAckResponse(BaseModel):
    session_id: str
    status: str
    chunk_index: int
    duration_ms: int | None
    chunk_count: int
    accepted: bool


class RealtimeSessionCloseResponse(BaseModel):
    session_id: str
    status: str
    chunk_count: int


class HealthResponse(BaseModel):
    status: str
    service: str
