"""
Centralised HTTP exception helpers.

All error responses use the shape: {"error": {"code", "message", "details"}}
No stack traces or internal details are ever returned to clients.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


def error_response(code: str, message: str, details: object = None, status: int = 400) -> JSONResponse:
    """Build a standard error JSON response."""
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details}},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Generic handler registered on the FastAPI app for HTTPException."""
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return error_response(
            code=f"http_{exc.status_code}",
            message=exc.detail,
            status=exc.status_code,
        )
    return error_response("internal_error", "An unexpected error occurred.", status=500)
