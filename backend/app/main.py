"""
HireLens FastAPI application factory.

Responsibilities:
- Create the FastAPI app instance with metadata
- Register CORS middleware (allow-list from settings)
- Attach SlowAPI rate limiter
- Mount the v1 API router
- Register Section 8 standardized exception handlers
- Expose the app for uvicorn: `uvicorn app.main:app --reload --port 8000`
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import settings, validate_jwt_secret_for_startup
from app.core.exceptions import (
    generic_exception_handler,
    http_exception_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.tasks.processing import recover_stuck_resumes

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager enforcing startup security checks and resume recovery."""
    validate_jwt_secret_for_startup()
    recover_stuck_resumes()
    yield


app = FastAPI(
    title="HireLens API",
    description="AI-Powered Resume Screening and Candidate Ranking Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Attach SlowAPI limiter state and middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS — allow-listed to the frontend origin only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Section 8 standardized exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(api_router, prefix=settings.api_v1_prefix)
