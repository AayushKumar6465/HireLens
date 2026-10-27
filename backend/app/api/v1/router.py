"""
Main API v1 router. Includes all sub-routers from Phase 1 and Phase 2.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, health, jobs, resumes, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["ops"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
