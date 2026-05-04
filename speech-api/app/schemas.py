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


class MeetingChunkResponse(BaseModel):
    id: str
    index: int
    start_time: str
    end_time: str
    status: str
    text: str | None = None
    error: str | None = None


class MeetingJobResponse(BaseModel):
    job_id: str
    file_name: str
    status: str
    progress: int
    total_chunks: int
    completed_chunks: int
    error: str | None = None
    chunks: list[MeetingChunkResponse]


class MeetingChunksResponse(BaseModel):
    job_id: str
    chunks: list[MeetingChunkResponse]
