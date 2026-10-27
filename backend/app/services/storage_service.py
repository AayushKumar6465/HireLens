"""
Secure private file storage service.

Responsibilities:
- Manage private storage of uploaded resume files outside static/public routes.
- Generate server UUID filenames to completely isolate user input from disk paths.
- Enforce strict path traversal prevention on all retrieval and deletion operations.
- Safely clean up files on disk during resume deletion or failed processing.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import get_logger, log_event

logger = get_logger(__name__)


def get_storage_dir() -> Path:
    """Return the absolute Path to the private storage directory, creating it if needed."""
    upload_path = Path(settings.upload_dir)
    if not upload_path.is_absolute():
        backend_dir = Path(__file__).resolve().parent.parent.parent
        upload_path = (backend_dir / upload_path).resolve()
    else:
        upload_path = upload_path.resolve()
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def validate_stored_filename(stored_filename: str) -> Path:
    """
    Validate that the stored filename is a safe, strictly confined file path.

    Prevents directory traversal attacks by ensuring the resolved path
    resides strictly within the configured storage directory.
    """
    # Strict regex: UUID hex with standard extension
    if not re.match(r"^[0-9a-fA-F-]{32,36}\.(pdf|docx)$", stored_filename):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "bad_request",
                "message": "Invalid stored filename format.",
            },
        )

    storage_dir = get_storage_dir()
    resolved_path = (storage_dir / stored_filename).resolve()

    try:
        resolved_path.relative_to(storage_dir)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "bad_request",
                "message": "Path traversal attempt detected.",
            },
        ) from None

    return resolved_path


def save_file(content: bytes, extension: str) -> tuple[str, Path]:
    """
    Persist uploaded file bytes under a server-generated UUID filename.

    Returns a tuple of (stored_filename, resolved_file_path).
    """
    normalized_ext = extension.lower().strip()
    if not normalized_ext.startswith("."):
        normalized_ext = f".{normalized_ext}"

    if normalized_ext not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "Unsupported file extension."},
        )

    stored_filename = f"{uuid.uuid4().hex}{normalized_ext}"
    storage_dir = get_storage_dir()
    target_path = storage_dir / stored_filename

    try:
        target_path.write_bytes(content)
    except Exception as exc:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        log_event(logger, "storage_save_failed")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "internal_error",
                "message": "Failed to save file to disk.",
            },
        ) from exc

    return stored_filename, target_path


def delete_file(stored_filename: str) -> bool:
    """
    Safely delete a stored file from disk by its stored filename.

    Returns True if the file was deleted, False if it was not found.
    """
    try:
        path = validate_stored_filename(stored_filename)
        if path.is_file():
            path.unlink()
            log_event(logger, "storage_file_deleted")
            return True
        return False
    except HTTPException:
        raise
    except Exception as exc:
        log_event(logger, "storage_delete_failed")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "internal_error",
                "message": "Failed to delete file from disk.",
            },
        ) from exc


def sanitize_download_filename(filename: str, fallback_ext: str = ".pdf") -> str:
    """
    Sanitize client original filename for safe Content-Disposition headers.

    Strips directory paths, control characters, quotes, and newlines to prevent header injection.
    """
    # Keep only base filename
    clean_name = Path(filename).name
    # Strip any newlines, carriage returns, and quotes
    clean_name = re.sub(r'[\r\n"\\/;:]', "", clean_name).strip()
    if not clean_name:
        clean_name = f"resume{fallback_ext}"
    return clean_name
