"""
Background resume processing task.

Orchestrates: parse → score → update status.
On app startup, resumes stuck in 'processing' for > 10 minutes are marked failed.
Implemented in Phase 2.
"""
