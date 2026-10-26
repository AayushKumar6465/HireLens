"""
Centralised HTTP exception helpers and handlers following Section 8 specification.

All error responses strictly use the shape:
{
    "error": {
        "code": "<error_code>",
        "message": "<human_readable_message>",
        "details": <optional_details_dict_or_list_or_null>
    }
}

No internal tracebacks, SQL statements, or sensitive details are ever exposed.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

STATUS_CODE_MAP = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limit_exceeded",
    500: "internal_error",
}


def error_response(
    code: str,
    message: str,
    details: Any = None,
    status: int = 400,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build a standard Section 8 error JSON response."""
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details}},
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions cleanly in Section 8 shape."""
    status = exc.status_code
    default_code = STATUS_CODE_MAP.get(status, f"http_{status}")

    if isinstance(exc.detail, dict):
        code = str(exc.detail.get("code", default_code))
        message = str(exc.detail.get("message", "An error occurred."))
        details = exc.detail.get("details", None)
    else:
        code = default_code
        message = str(exc.detail) if exc.detail else "An error occurred."
        details = None

    return error_response(
        code=code, message=message, details=details, status=status, headers=exc.headers
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Format 422 Pydantic schema validation errors into standard Section 8 error format."""
    clean_errors = []
    for err in exc.errors():
        clean_errors.append(
            {
                "loc": [str(x) for x in err.get("loc", [])],
                "msg": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )

    return error_response(
        code="validation_error",
        message="Request validation failed.",
        details=clean_errors,
        status=422,
    )


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Format 429 slowapi rate limit exceeded errors into Section 8 error format with Retry-After header."""
    headers = {}
    # SlowAPI provides retry_after or detail info
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        headers["Retry-After"] = str(int(retry_after))

    return error_response(
        code="rate_limit_exceeded",
        message="Too many requests. Please try again later.",
        details=None,
        status=429,
        headers=headers if headers else None,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled exception handler ensuring no internal stack traces leak."""
    return error_response(
        code="internal_error",
        message="An unexpected server error occurred.",
        details=None,
        status=500,
    )
