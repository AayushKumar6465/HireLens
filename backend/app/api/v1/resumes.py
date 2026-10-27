"""
Resume upload, file download, status polling, and deletion endpoints (/api/v1/resumes).

Endpoints:
- POST /upload: Bulk upload PDF/DOCX resumes with rate limiting (200 OK)
- GET /{id}: Resume details and metadata (200 OK)
- GET /{id}/status: Resume parsing status polling (200 OK)
- GET /{id}/file: Authenticated binary file download (200 OK)
- DELETE /{id}: Owner-scoped resume and disk file deletion (204 No Content)

Ownership:
- All operations strictly owner-scoped via Candidate.owner_id == current_user.id.
- Foreign resumes return HTTP 404 (admins cannot bypass).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, log_event
from app.core.rate_limit import limiter
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import (
    BatchUploadResponse,
    ResumeDuplicateItemResult,
    ResumeFailedItemResult,
    ResumeResponse,
    ResumeStatusResponse,
    ResumeUploadItemResult,
)
from app.services import storage_service, upload_validator
from app.services.upload_validator import FileValidationError
from app.tasks.processing import process_resume_task

logger = get_logger(__name__)

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/upload",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload multiple resume documents (PDF/DOCX)",
)
@limiter.limit("20/minute")
def upload_resumes(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    files: Annotated[
        list[UploadFile], File(description="1-20 PDF or DOCX resume documents")
    ],
    background_tasks: BackgroundTasks,
    job_id: Annotated[
        uuid.UUID | None, Form(description="Optional target job ID")
    ] = None,
) -> BatchUploadResponse:
    """
    Validate, store, and register a batch of uploaded resumes.

    Enforces:
    - Max 20 files per batch
    - Max 5 MB per file
    - PDF/DOCX magic bytes and structural checks
    - Duplicate detection by SHA-256 (reports duplicate, never silently drops)
    - Ownership verification if job_id is provided (foreign job ID returns 404)
    """
    upload_validator.validate_batch_size(files)

    # Verify job ownership if job_id is provided
    if job_id is not None:
        target_job = (
            db.query(Job)
            .filter(Job.id == job_id, Job.owner_id == current_user.id)
            .first()
        )
        if target_job is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": "Job not found."},
            )

    uploaded: list[ResumeUploadItemResult] = []
    duplicates: list[ResumeDuplicateItemResult] = []
    failed: list[ResumeFailedItemResult] = []

    for file in files:
        original_name = file.filename or "unknown"
        try:
            validated = upload_validator.validate_file(file)
        except FileValidationError as fve:
            failed.append(
                ResumeFailedItemResult(
                    original_filename=original_name,
                    error_code=fve.error_code,
                    message=fve.message,
                )
            )
            continue
        except (OSError, ValueError, RuntimeError):
            log_event(logger, "upload_unexpected_error")
            failed.append(
                ResumeFailedItemResult(
                    original_filename=original_name,
                    error_code="internal_error",
                    message="An unexpected error occurred while validating the file.",
                )
            )
            continue

        # Check for duplicate upload by SHA-256 for this owner
        existing_resume = (
            db.query(Resume)
            .join(Candidate, Resume.candidate_id == Candidate.id)
            .filter(
                Candidate.owner_id == current_user.id, Resume.sha256 == validated.sha256
            )
            .first()
        )
        if existing_resume is not None:
            duplicates.append(
                ResumeDuplicateItemResult(
                    original_filename=validated.original_filename,
                    sha256=validated.sha256,
                    existing_resume_id=existing_resume.id,
                    message="Duplicate file detected. Already uploaded previously.",
                )
            )
            continue

        # Save to private storage with a server UUID filename
        try:
            stored_filename, _ = storage_service.save_file(
                validated.content, validated.extension
            )
        except HTTPException as he:
            detail = he.detail if isinstance(he.detail, dict) else {}
            failed.append(
                ResumeFailedItemResult(
                    original_filename=validated.original_filename,
                    error_code=str(detail.get("code", "storage_error")),
                    message=str(detail.get("message", "Failed to store file.")),
                )
            )
            continue

        # Create candidate entity to anchor the resume
        cleaned_stem = (
            Path(validated.original_filename)
            .stem.replace("_", " ")
            .replace("-", " ")
            .strip()
            .title()
        )
        candidate = Candidate(
            owner_id=current_user.id,
            full_name=cleaned_stem if cleaned_stem else "Candidate",
            status="new",
        )
        db.add(candidate)
        db.flush()

        # Create resume entity
        resume = Resume(
            candidate_id=candidate.id,
            job_id=job_id,
            original_filename=validated.original_filename,
            stored_filename=stored_filename,
            mime_type=validated.mime_type,
            size_bytes=validated.size_bytes,
            sha256=validated.sha256,
            parse_status="pending",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Dispatch asynchronous parsing task
        background_tasks.add_task(process_resume_task, resume.id)

        log_event(
            logger,
            "resume_uploaded",
            resume_id=str(resume.id),
            candidate_id=str(candidate.id),
            job_id=str(job_id) if job_id else None,
        )

        uploaded.append(
            ResumeUploadItemResult(
                resume_id=resume.id,
                candidate_id=candidate.id,
                original_filename=resume.original_filename,
                status="pending",
            )
        )

    return BatchUploadResponse(
        uploaded=uploaded,
        duplicates=duplicates,
        failed=failed,
        total_uploaded=len(uploaded),
        total_duplicates=len(duplicates),
        total_failed=len(failed),
    )


def _get_owner_scoped_resume(db: Session, user: User, resume_id: uuid.UUID) -> Resume:
    """
    Retrieve resume ensuring Candidate.owner_id == user.id.

    Returns HTTP 404 if foreign or non-existent (admins cannot bypass).
    """
    resume = (
        db.query(Resume)
        .join(Candidate, Resume.candidate_id == Candidate.id)
        .filter(Resume.id == resume_id, Candidate.owner_id == user.id)
        .first()
    )
    if resume is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resume not found."},
        )
    return resume


@router.get(
    "/{id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume details by ID",
)
def get_resume(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ResumeResponse:
    """Retrieve resume metadata and details. Returns 404 for foreign resumes."""
    resume = _get_owner_scoped_resume(db, current_user, id)
    resp = ResumeResponse.model_validate(resume)
    if resume.parsed_resume:
        pr = resume.parsed_resume
        resp.parsed_data = {
            "raw_text": pr.raw_text,
            "skills": pr.skills,
            "experience": pr.experience,
            "education": pr.education,
            "total_experience_years": pr.total_experience_years,
            "highest_degree": pr.highest_degree,
            "sections": pr.sections,
            "parser_version": pr.parser_version,
        }
    return resp


@router.get(
    "/{id}/status",
    response_model=ResumeStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume parsing status",
)
def get_resume_status(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ResumeStatusResponse:
    """Poll the processing status of an uploaded resume. Returns 404 for foreign resumes."""
    resume = _get_owner_scoped_resume(db, current_user, id)
    return ResumeStatusResponse.model_validate(resume)


@router.get(
    "/{id}/file",
    status_code=status.HTTP_200_OK,
    summary="Download original resume file (authenticated)",
)
def download_resume_file(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> FileResponse:
    """
    Stream the original resume document file to the authenticated owner.

    Enforces ownership and safe Content-Disposition headers. Returns 404 for foreign resumes.
    """
    resume = _get_owner_scoped_resume(db, current_user, id)
    target_path = storage_service.validate_stored_filename(resume.stored_filename)

    if not target_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "code": "not_found",
                "message": "Stored resume file not found on disk.",
            },
        )

    safe_filename = storage_service.sanitize_download_filename(resume.original_filename)

    log_event(logger, "resume_file_downloaded", resume_id=str(id))

    return FileResponse(
        path=str(target_path),
        media_type=resume.mime_type,
        filename=safe_filename,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume and its stored file",
)
def delete_resume(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """
    Delete a resume record and purge its physical file from disk.

    Enforces owner scoping. Returns 404 for foreign resumes.
    """
    resume = _get_owner_scoped_resume(db, current_user, id)
    candidate = resume.candidate
    stored_filename = resume.stored_filename

    # Delete physical file from disk
    storage_service.delete_file(stored_filename)

    # Delete resume record from database
    db.delete(resume)
    db.commit()

    # Clean up candidate if no other resumes remain
    if candidate:
        remaining = db.query(Resume).filter(Resume.candidate_id == candidate.id).count()
        if remaining == 0:
            db.delete(candidate)
            db.commit()

    log_event(logger, "resume_deleted", resume_id=str(id), user_id=str(current_user.id))
