from pathlib import Path

import httpx


class WhisperService:
    def __init__(self, api_key: str, model_id: str) -> None:
        self.api_key = api_key
        self.model_id = model_id

    def transcribe(self, file_path: str, language: str | None = None) -> dict:
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not configured")

        endpoint = "https://api.elevenlabs.io/v1/speech-to-text"
        payload = {"model_id": self.model_id}
        if language:
            payload["language_code"] = language

        suffix = Path(file_path).suffix.lower() or ".bin"
        content_type = "audio/mpeg"
        if suffix in {".wav"}:
            content_type = "audio/wav"
        elif suffix in {".m4a"}:
            content_type = "audio/mp4"
        elif suffix in {".webm"}:
            content_type = "audio/webm"
        elif suffix in {".mp4"}:
            content_type = "video/mp4"

        with open(file_path, "rb") as audio_file:
            files = {"file": (Path(file_path).name, audio_file, content_type)}
            headers = {"xi-api-key": self.api_key}
            response = httpx.post(
                endpoint,
                data=payload,
                files=files,
                headers=headers,
                timeout=120,
            )

        response.raise_for_status()
        result = response.json()

        return {
            "text": result.get("text", "").strip(),
            "language": result.get("language_code") or result.get("language"),
            "duration": result.get("duration"),
            "segments": result.get("segments") or [],
        }
