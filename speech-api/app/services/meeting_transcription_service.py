from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.services.whisper_service import WhisperService
from app.utils.ffmpeg_utils import extract_audio_from_video, split_audio_into_chunks
from app.utils.file_utils import delete_file_safely


class MeetingTranscriptionService:
    """In-memory meeting transcription workflow service for chunked video transcription."""

    def __init__(self, whisper_service: WhisperService, upload_dir: str, chunk_seconds: int = 300) -> None:
        self.whisper_service = whisper_service
        self.upload_dir = Path(upload_dir)
        self.chunk_seconds = chunk_seconds
        self.jobs: dict[str, dict] = {}
        self._lock = Lock()

    def create_job(self, file_path: str, file_name: str) -> dict:
        job_id = str(uuid4())
        now = datetime.now(timezone.utc)
        job = {
            "job_id": job_id,
            "file_name": file_name,
            "file_path": file_path,
            "status": "queued",
            "progress": 0,
            "total_chunks": 0,
            "completed_chunks": 0,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "chunks": [],
        }
        with self._lock:
            self.jobs[job_id] = job
        return self._public_job(job)

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            return self._public_job(job)

    def get_chunks(self, job_id: str) -> list[dict] | None:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            return [self._public_chunk(chunk) for chunk in job["chunks"]]

    def process_job(self, job_id: str) -> None:
        audio_path: str | None = None
        chunks_dir: Path | None = None
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            self._update_job(job_id, status="processing", progress=0, error=None)
            video_path = job["file_path"]
            audio_path = str(self.upload_dir / f"{job_id}_audio.wav")
            chunks_dir = self.upload_dir / f"{job_id}_chunks"

            extract_audio_from_video(video_path, audio_path)
            chunks = split_audio_into_chunks(audio_path, str(chunks_dir), chunk_seconds=self.chunk_seconds)

            if not chunks:
                raise RuntimeError("No audio chunks were generated from the uploaded video.")

            prepared_chunks = [
                {
                    **chunk,
                    "status": "pending",
                    "text": None,
                    "error": None,
                }
                for chunk in chunks
            ]
            self._update_job(job_id, chunks=prepared_chunks, total_chunks=len(prepared_chunks))

            for index, chunk in enumerate(prepared_chunks):
                self._set_chunk_status(job_id, index, status="processing")
                try:
                    result = self.whisper_service.transcribe(chunk["file_path"])
                    chunk_text = (result.get("text") or "").strip()
                    self._set_chunk_status(job_id, index, status="done", text=chunk_text, error=None)
                except Exception as exc:
                    self._set_chunk_status(job_id, index, status="failed", error=str(exc))
                finally:
                    self._increment_progress(job_id)

            final_job = self.jobs.get(job_id)
            if final_job:
                job_status = "completed" if final_job["total_chunks"] > 0 else "failed"
                self._update_job(job_id, status=job_status)
        except Exception as exc:
            self._update_job(job_id, status="failed", error=str(exc))
        finally:
            delete_file_safely(self.jobs.get(job_id, {}).get("file_path"))
            delete_file_safely(audio_path)
            if chunks_dir and chunks_dir.exists():
                for chunk_file in chunks_dir.glob("chunk_*.wav"):
                    delete_file_safely(str(chunk_file))
                chunks_dir.rmdir()

    def _update_job(self, job_id: str, **updates: object) -> None:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job.update(updates)
            job["updated_at"] = datetime.now(timezone.utc)

    def _set_chunk_status(self, job_id: str, index: int, **updates: object) -> None:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            chunk = job["chunks"][index]
            chunk.update(updates)
            job["updated_at"] = datetime.now(timezone.utc)

    def _increment_progress(self, job_id: str) -> None:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job["completed_chunks"] += 1
            total = max(job["total_chunks"], 1)
            job["progress"] = int((job["completed_chunks"] / total) * 100)
            job["updated_at"] = datetime.now(timezone.utc)

    def _public_job(self, job: dict) -> dict:
        return {
            "job_id": job["job_id"],
            "file_name": job["file_name"],
            "status": job["status"],
            "progress": job["progress"],
            "total_chunks": job["total_chunks"],
            "completed_chunks": job["completed_chunks"],
            "error": job["error"],
            "chunks": [self._public_chunk(chunk) for chunk in job["chunks"]],
        }

    @staticmethod
    def _public_chunk(chunk: dict) -> dict:
        return {
            "id": chunk["id"],
            "index": chunk["index"],
            "start_time": chunk["start_time"],
            "end_time": chunk["end_time"],
            "status": chunk["status"],
            "text": chunk.get("text"),
            "error": chunk.get("error"),
        }
