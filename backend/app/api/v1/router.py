"""
Main API v1 router. Includes all sub-routers from Phase 1+.

Currently only the health sub-router is mounted.
"""

from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["ops"])
