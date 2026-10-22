# Architecture

HireLens follows a modular monolith architecture: one FastAPI backend, one React frontend, and a single PostgreSQL database hosted on Neon — connected by a JSON REST API under `/api/v1`. See the data-flow description in `PROJECT_PLAN.md` Section 5.
