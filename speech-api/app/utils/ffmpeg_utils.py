from __future__ import annotations

from pathlib import Path
import subprocess


def _format_seconds(seconds: float) -> str:
    total = max(int(round(seconds)), 0)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _get_audio_duration_seconds(audio_path: str) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to inspect chunk duration with ffprobe: {result.stderr.strip() or result.stdout.strip()}"
        )

    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("ffprobe returned an invalid duration value.") from exc


def extract_audio_from_video(video_path: str, output_audio_path: str) -> None:
    """Extract mono 16kHz WAV audio from a video file using ffmpeg."""
    command = ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", output_audio_path]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to extract audio with ffmpeg: {result.stderr.strip() or result.stdout.strip()}"
        )


def split_audio_into_chunks(audio_path: str, output_dir: str, chunk_seconds: int = 300) -> list[dict]:
    """Split WAV audio into fixed-size chunks and return chunk metadata with actual durations."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    chunk_pattern = str(output_path / "chunk_%03d.wav")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        audio_path,
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-c",
        "copy",
        chunk_pattern,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to split audio with ffmpeg: {result.stderr.strip() or result.stdout.strip()}"
        )

    chunk_files = sorted(output_path.glob("chunk_*.wav"))
    chunks: list[dict] = []
    current_start_seconds = 0.0
    for index, chunk_file in enumerate(chunk_files):
        duration_seconds = _get_audio_duration_seconds(str(chunk_file))
        end_seconds = current_start_seconds + duration_seconds
        chunks.append(
            {
                "id": chunk_file.stem,
                "index": index,
                "file_path": str(chunk_file),
                "start_time": _format_seconds(current_start_seconds),
                "end_time": _format_seconds(end_seconds),
                "duration_seconds": duration_seconds,
            }
        )
        current_start_seconds = end_seconds

    return chunks
