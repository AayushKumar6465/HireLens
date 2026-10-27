"""
Isolated standalone resume parsing worker executed in a child process.

Enables hard process termination on Windows if parsing exceeds the 30-second timeout.
Usage:
    python -m app.tasks.parse_worker <resume_id>
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from fastapi import HTTPException

from app.core.logging import get_logger, log_event
from app.db.session import SessionLocal
from app.models.candidate import Candidate
from app.models.resume import ParsedResume, Resume
from app.services import storage_service
from app.services.parsing.extractor import ParsingError, ScannedOrEmptyError
from app.services.parsing.pipeline import parse_resume_document

logger = get_logger(__name__)


def run_worker(resume_id_str: str) -> int:
    """Execute parsing in this process for the given resume_id."""
    try:
        resume_id = uuid.UUID(resume_id_str)
    except ValueError:
        logger.error("Invalid resume UUID provided to worker: %s", resume_id_str)
        return 1

    if SessionLocal is None:
        logger.error("SessionLocal database session is not configured")
        return 1

    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error("Resume not found in database: %s", resume_id)
            return 1

        # Resolve storage path
        try:
            file_path = storage_service.validate_stored_filename(resume.stored_filename)
        except (HTTPException, OSError, ValueError):
            resume.parse_status = "failed"
            resume.parse_error = "file_missing"
            db.commit()
            return 0

        if not file_path.is_file():
            resume.parse_status = "failed"
            resume.parse_error = "file_missing"
            db.commit()
            return 0

        # Execute parsing pipeline
        ext = Path(resume.stored_filename).suffix
        parsed = parse_resume_document(
            file_path, ext, original_filename=resume.original_filename
        )

        # Upsert ParsedResume record
        parsed_record = (
            db.query(ParsedResume).filter(ParsedResume.resume_id == resume.id).first()
        )
        if not parsed_record:
            parsed_record = ParsedResume(
                resume_id=resume.id,
                raw_text=parsed.raw_text,
                skills=parsed.skills,
                experience=parsed.experience,
                education=parsed.education,
                total_experience_years=parsed.total_experience_years,
                highest_degree=parsed.highest_degree,
                sections=parsed.sections,
                parser_version=parsed.parser_version,
            )
            db.add(parsed_record)
        else:
            parsed_record.raw_text = parsed.raw_text
            parsed_record.skills = parsed.skills
            parsed_record.experience = parsed.experience
            parsed_record.education = parsed.education
            parsed_record.total_experience_years = parsed.total_experience_years
            parsed_record.highest_degree = parsed.highest_degree
            parsed_record.sections = parsed.sections
            parsed_record.parser_version = parsed.parser_version

        # Update Candidate details if placeholder
        candidate = (
            db.query(Candidate).filter(Candidate.id == resume.candidate_id).first()
        )
        if candidate:
            contact = parsed.contact_info
            if contact.get("full_name"):
                candidate.full_name = contact["full_name"]
            if contact.get("email") and not candidate.email:
                candidate.email = contact["email"]
            if contact.get("phone") and not candidate.phone:
                candidate.phone = contact["phone"]
            if contact.get("links") and not candidate.links:
                candidate.links = contact["links"]

        resume.parse_status = "done"
        resume.parse_error = None
        db.commit()
        log_event(logger, "resume_parsed_success", resume_id=str(resume.id))
        return 0

    except ScannedOrEmptyError:
        db.rollback()
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.parse_status = "failed"
            resume.parse_error = "scanned_or_empty"
            db.commit()
            log_event(logger, "resume_scanned_or_empty", resume_id=str(resume.id))
        return 0

    except ParsingError as pe:
        db.rollback()
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.parse_status = "failed"
            resume.parse_error = pe.error_code
            db.commit()
            log_event(logger, "resume_parse_error", resume_id=str(resume.id))
        return 0

    except (OSError, RuntimeError, ValueError) as exc:
        db.rollback()
        logger.error("Unexpected worker exception: %s", exc)
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.parse_status = "failed"
            resume.parse_error = "corrupted_file"
            db.commit()
            log_event(logger, "resume_parse_exception", resume_id=str(resume.id))
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    sys.exit(run_worker(sys.argv[1]))
