"""
Upload validation and security inspection service.

Enforces:
- File size cap (<= 5 MB per file)
- Batch upload limit (<= 20 files per batch)
- Extension allow-list (.pdf, .docx)
- Magic byte verification using python-magic
- DOCX ZIP-bomb protection (entry count, uncompressed size, compression ratio)
- PDF page count cap (<= 20 pages) and structure validation
- Empty / corrupted file rejection
- SHA-256 computation for duplicate detection
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

import magic
import pymupdf
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.logging import get_logger, log_event

logger = get_logger(__name__)

# Resource limits
MAX_FILE_BYTES = settings.max_upload_mb * 1024 * 1024  # 5 MB
MAX_BATCH_FILES = settings.max_files_per_batch  # 20 files
MAX_DOCX_ENTRIES = 100
MAX_DOCX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_DOCX_COMPRESSION_RATIO = 50.0  # 50:1
MAX_PDF_PAGES = 20

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@dataclass
class ValidatedFile:
    """Container for a successfully validated and inspected uploaded document."""

    original_filename: str
    extension: str
    content: bytes
    size_bytes: int
    sha256: str
    mime_type: str


class FileValidationError(Exception):
    """Exception raised when an individual file fails security or format validation."""

    def __init__(self, error_code: str, message: str) -> None:
        self.error_code = error_code
        self.message = message
        super().__init__(message)


def validate_batch_size(files: list[UploadFile]) -> None:
    """Validate that the incoming batch size does not exceed limits or arrive empty."""
    if not files:
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "No files provided for upload."},
        )

    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "batch_too_large",
                "message": f"Maximum of {MAX_BATCH_FILES} files allowed per upload batch.",
            },
        )


def _validate_pdf_structure(content: bytes) -> None:
    """Validate PDF header and page count limits via PyMuPDF."""
    if not content.startswith(b"%PDF-"):
        raise FileValidationError(
            "corrupted_file",
            "File header does not match valid PDF structure.",
        )

    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
        page_count = len(doc)
        doc.close()
    except Exception as exc:
        raise FileValidationError(
            "corrupted_file",
            "PDF document is malformed or unreadable.",
        ) from exc

    if page_count > MAX_PDF_PAGES:
        raise FileValidationError(
            "pdf_page_limit_exceeded",
            f"PDF exceeds maximum allowed length of {MAX_PDF_PAGES} pages (contains {page_count}).",
        )


def _validate_docx_structure(content: bytes) -> None:
    """Validate DOCX ZIP packaging and enforce anti-ZIP-bomb safeguards."""
    try:
        zip_buffer = io.BytesIO(content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            infolist = zf.infolist()
            entry_count = len(infolist)

            if entry_count > MAX_DOCX_ENTRIES:
                raise FileValidationError(
                    "corrupt_or_malicious_docx",
                    f"DOCX entry count ({entry_count}) exceeds safety limit ({MAX_DOCX_ENTRIES}).",
                )

            total_compressed = 0
            total_uncompressed = 0
            has_document_xml = False

            for info in infolist:
                # Disallow path traversal entries inside zip
                if ".." in info.filename or info.filename.startswith(("/", "\\")):
                    raise FileValidationError(
                        "corrupt_or_malicious_docx",
                        "DOCX archive contains illegal file paths.",
                    )

                if info.filename in {"word/document.xml", "[Content_Types].xml"}:
                    has_document_xml = True

                total_compressed += info.compress_size
                total_uncompressed += info.file_size

                if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise FileValidationError(
                        "corrupt_or_malicious_docx",
                        "DOCX uncompressed payload exceeds maximum size limit (20 MB).",
                    )

            if not has_document_xml:
                raise FileValidationError(
                    "corrupted_file",
                    "DOCX structure is invalid: missing word/document.xml or [Content_Types].xml.",
                )

            # Check compression ratio
            ratio = total_uncompressed / max(total_compressed, 1)
            if ratio > MAX_DOCX_COMPRESSION_RATIO:
                raise FileValidationError(
                    "corrupt_or_malicious_docx",
                    f"Suspicious compression ratio ({ratio:.1f}:1) detected in DOCX archive.",
                )
    except zipfile.BadZipFile as exc:
        raise FileValidationError(
            "corrupted_file",
            "DOCX file is corrupt or not a valid ZIP container.",
        ) from exc


def validate_file(file: UploadFile) -> ValidatedFile:
    """
    Validate, inspect, and hash a single uploaded file.

    Raises FileValidationError if validation fails.
    """
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            "unsupported_extension",
            f"Unsupported file extension '{ext}'. Only .pdf and .docx are allowed.",
        )

    # Read content chunk by chunk enforcing MAX_FILE_BYTES
    content_chunks = []
    total_bytes = 0

    while True:
        chunk = file.file.read(65536)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_FILE_BYTES:
            raise FileValidationError(
                "file_too_large",
                f"File size exceeds the 5 MB limit (read > {total_bytes} bytes).",
            )
        content_chunks.append(chunk)

    if total_bytes == 0:
        raise FileValidationError("empty_file", "File is empty (0 bytes).")

    content = b"".join(content_chunks)

    # Detect MIME type via magic bytes
    try:
        detected_mime = magic.from_buffer(content, mime=True)
    except Exception as exc:
        log_event(logger, "magic_byte_detection_error")
        raise FileValidationError(
            "corrupted_file",
            "Failed to determine document file type.",
        ) from exc

    # Validate according to extension and detected MIME
    if ext == ".pdf":
        if detected_mime != "application/pdf" and not content.startswith(b"%PDF-"):
            raise FileValidationError(
                "fake_file_extension",
                f"File extension is .pdf but content type was detected as '{detected_mime}'.",
            )
        _validate_pdf_structure(content)
        canonical_mime = "application/pdf"

    elif ext == ".docx":
        valid_docx_mimes = {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/zip",
            "application/octet-stream",
        }
        if detected_mime not in valid_docx_mimes:
            raise FileValidationError(
                "fake_file_extension",
                f"File extension is .docx but content type was detected as '{detected_mime}'.",
            )
        _validate_docx_structure(content)
        canonical_mime = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    else:
        raise FileValidationError(
            "unsupported_extension", f"Unsupported extension: {ext}"
        )

    sha256 = hashlib.sha256(content).hexdigest()

    return ValidatedFile(
        original_filename=filename,
        extension=ext,
        content=content,
        size_bytes=total_bytes,
        sha256=sha256,
        mime_type=canonical_mime,
    )
