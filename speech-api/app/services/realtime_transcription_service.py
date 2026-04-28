from datetime import datetime, timezone
from uuid import uuid4


class RealtimeTranscriptionService:
    """Session manager for future chunk-based realtime transcription.

    This service currently stores lightweight session/chunk metadata in-memory
    so that transport layers (HTTP now, WebSocket later) can share the same
    business workflow.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def create_session(self, language: str | None = None) -> dict:
        session_id = str(uuid4())
        now = datetime.now(timezone.utc)
        session = {
            "session_id": session_id,
            "status": "active",
            "language": language,
            "chunk_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        self._sessions[session_id] = session
        return session

    def append_chunk(self, session_id: str, chunk_index: int, duration_ms: int | None = None) -> dict:
        session = self._get_session_or_raise(session_id)
        session["chunk_count"] += 1
        session["updated_at"] = datetime.now(timezone.utc)
        return {
            "session_id": session_id,
            "status": session["status"],
            "chunk_index": chunk_index,
            "duration_ms": duration_ms,
            "chunk_count": session["chunk_count"],
            "accepted": True,
        }

    def close_session(self, session_id: str) -> dict:
        session = self._get_session_or_raise(session_id)
        session["status"] = "closed"
        session["updated_at"] = datetime.now(timezone.utc)
        return session

    def get_session(self, session_id: str) -> dict:
        return self._get_session_or_raise(session_id)

    def _get_session_or_raise(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Realtime session not found: {session_id}")
        return session
