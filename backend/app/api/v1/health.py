"""
Health check endpoint: GET /api/v1/health

Returns application status and database connectivity.
Database check uses SELECT 1 via the sync engine; does not expose credentials.
"""

from fastapi import APIRouter

from app.db.session import check_database_connection

router = APIRouter()


@router.get("", summary="Health check")
def health_check() -> dict:
    """
    Return overall application health.

    Response shape:
        {
            "status": "ok" | "degraded",
            "database": "connected" | "unreachable" | "not_configured"
        }
    """
    db_ok = check_database_connection()
    db_status = "connected" if db_ok else "unreachable"

    if not db_ok:
        from app.core.config import settings
        if not settings.database_url:
            db_status = "not_configured"

    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_status,
    }
