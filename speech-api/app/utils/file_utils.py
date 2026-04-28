from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".webm", ".m4a", ".mp4"}
ALLOWED_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/mp4",
    "audio/x-m4a",
    "video/mp4",
    "video/webm",
}


def validate_file_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {extension}",
        )
    return extension


def validate_content_type(content_type: str | None) -> None:
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {content_type}",
        )


async def validate_file_size(file: UploadFile, max_size_mb: int) -> None:
    max_size_bytes = max_size_mb * 1024 * 1024
    await file.seek(0)
    contents = await file.read()
    size = len(contents)
    await file.seek(0)

    if size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large. Max size is {max_size_mb} MB",
        )


async def save_upload_file(file: UploadFile, upload_dir: str) -> str:
    extension = validate_file_extension(file.filename or "")
    validate_content_type(file.content_type)

    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid4()}{extension}"
    file_path = upload_path / file_name

    await file.seek(0)
    with file_path.open("wb") as out_file:
        out_file.write(await file.read())
    await file.seek(0)

    return str(file_path)


def delete_file_safely(file_path: str | None) -> None:
    if not file_path:
        return

    path = Path(file_path)
    if path.exists():
        path.unlink()
