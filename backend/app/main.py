"""
HireLens FastAPI application factory.

Responsibilities:
- Create the FastAPI app instance with metadata
- Register CORS middleware (allow-list from settings)
- Mount the v1 API router
- Register exception handlers
- Expose the app for uvicorn: `uvicorn app.main:app --reload --port 8000`
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import http_exception_handler
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="HireLens API",
    description="AI-Powered Resume Screening and Candidate Ranking Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow-listed to the frontend origin only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)

app.include_router(api_router, prefix=settings.api_v1_prefix)
