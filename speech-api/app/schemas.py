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


class HealthResponse(BaseModel):
    status: str
    service: str
