from faster_whisper import WhisperModel


class WhisperService:
    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, file_path: str, language: str | None = None) -> dict:
        segments, info = self.model.transcribe(
            file_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )

        segment_list: list[dict] = []
        full_text_parts: list[str] = []
        for segment in segments:
            text = segment.text.strip()
            segment_list.append(
                {
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": text,
                }
            )
            if text:
                full_text_parts.append(text)

        return {
            "text": " ".join(full_text_parts).strip(),
            "language": getattr(info, "language", None),
            "duration": float(info.duration) if getattr(info, "duration", None) is not None else None,
            "segments": segment_list,
        }
