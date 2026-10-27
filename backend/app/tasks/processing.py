"""
Background resume processing and recovery tasks.

Orchestrates:
- Asynchronous parsing dispatch with atomic state acquisition
- Hard 30-second execution timeout via isolated child process
- Application startup recovery for pending or interrupted resumes
"""

from __future__ import annotations

import datetime
import subprocess
import sys
import uuid
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import and_, func

from app.core.logging import get_logger, log_event
from app.db.session import SessionLocal
from app.models.resume import Resume
from app.services import storage_service

logger = get_logger(__name__)

PARSING_TIMEOUT_SECONDS = 30.0
STUCK_PROCESSING_MINUTES = 10


def process_resume_task(resume_id: uuid.UUID) -> None:
    """
    Background task worker to transition and parse a resume document.

    Enforces:
    - Atomic transition from 'pending' to 'processing'
    - Hard 30-second OS-level subprocess timeout with process termination
    - Failure capture and safe error codes (no PII logged)
    """
    if SessionLocal is None:
        logger.error("SessionLocal database session is not configured")
        return

    db = SessionLocal()
    backend_dir = Path(__file__).resolve().parent.parent.parent

    try:
        # Atomic transition to 'processing' to prevent concurrent duplicate runs
        updated_rows = (
            db.query(Resume)
            .filter(Resume.id == resume_id, Resume.parse_status == "pending")
            .update(
                {"parse_status": "processing", "updated_at": func.now()},
                synchronize_session=False,
            )
        )
        db.commit()

        if updated_rows == 0:
            # Another task or recovery process has already claimed this resume
            return

        log_event(logger, "resume_processing_started", resume_id=str(resume_id))

        # Launch isolated subprocess with hard 30-second timeout
        cmd = [sys.executable, "-m", "app.tasks.parse_worker", str(resume_id)]
        try:
            res = subprocess.run(
                cmd,
                cwd=str(backend_dir),
                timeout=PARSING_TIMEOUT_SECONDS,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                logger.error(
                    "Parse worker exited with non-zero code %d: %s",
                    res.returncode,
                    res.stderr,
                )
        except subprocess.TimeoutExpired:
            log_event(logger, "resume_parse_timeout", resume_id=str(resume_id))
            db.query(Resume).filter(Resume.id == resume_id).update(
                {
                    "parse_status": "failed",
                    "parse_error": "timeout",
                    "updated_at": func.now(),
                },
                synchronize_session=False,
            )
            db.commit()

    except (OSError, RuntimeError, ValueError) as exc:
        logger.error("Error in process_resume_task for %s: %s", resume_id, exc)
        db.rollback()
        db.query(Resume).filter(Resume.id == resume_id).update(
            {
                "parse_status": "failed",
                "parse_error": "internal_error",
                "updated_at": func.now(),
            },
            synchronize_session=False,
        )
        db.commit()
    finally:
        db.close()


def recover_stuck_resumes() -> None:
    """
    Recover orphaned or stuck resumes during application startup.

    1. Resumes in 'processing' for > 10 minutes -> marked 'failed' with reason 'interrupted'.
    2. Resumes in 'pending' -> re-dispatched for processing if file exists on disk,
       or marked 'failed' with 'file_missing' if storage file is absent.
    """
    if SessionLocal is None:
        return

    db = SessionLocal()
    try:
        cutoff_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(
            minutes=STUCK_PROCESSING_MINUTES
        )

        # 1. Recover resumes stuck in 'processing' > 10 minutes
        stuck_resumes = (
            db.query(Resume)
            .filter(
                and_(
                    Resume.parse_status == "processing",
                    Resume.updated_at < cutoff_time,
                )
            )
            .all()
        )

        for r in stuck_resumes:
            r.parse_status = "failed"
            r.parse_error = "interrupted"
            log_event(logger, "resume_recovery_interrupted", resume_id=str(r.id))

        db.commit()

        # 2. Recover resumes left in 'pending' from a server restart
        pending_resumes = (
            db.query(Resume).filter(Resume.parse_status == "pending").all()
        )

        resumes_to_process: list[uuid.UUID] = []
        for r in pending_resumes:
            try:
                p = storage_service.validate_stored_filename(r.stored_filename)
                if p.is_file():
                    resumes_to_process.append(r.id)
                else:
                    r.parse_status = "failed"
                    r.parse_error = "file_missing"
                    log_event(
                        logger, "resume_recovery_missing_file", resume_id=str(r.id)
                    )
            except (HTTPException, OSError, ValueError):
                r.parse_status = "failed"
                r.parse_error = "file_missing"

        db.commit()

        # Process pending resumes during startup recovery
        for r_id in resumes_to_process:
            process_resume_task(r_id)

    except (OSError, RuntimeError, ValueError) as exc:
        logger.error("Failed during startup resume recovery: %s", exc)
        db.rollback()
    finally:
        db.close()
