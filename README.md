# HireLens

> AI-Powered Resume Screening and Candidate Ranking Platform 

HireLens lets recruiters create job openings, bulk-upload resumes (PDF/DOCX), parse them into structured data, and rank candidates against each job using an **explainable hybrid scoring engine** (skills, semantic similarity, experience, education).

---

## Features

- **Bulk resume upload** — drag-and-drop PDF/DOCX files, validated by size, magic bytes and extension
- **AI resume parsing** — skills (with evidence), experience (merged date ranges), education, contact info
- **Explainable candidate ranking** — every score comes with a full breakdown and matched/missing skill evidence
- **Hybrid scoring** — skills 40 %, semantic similarity 30 %, experience 20 %, education 10 % (configurable)
- **Recruiter pipeline** — status management (new → screened → shortlisted → interview → rejected) with confirm dialogs; no auto-rejection
- **Analytics dashboard** — score distribution, top skills, pipeline funnel
- **CSV export** — formula-injection sanitised
- **Dark mode**, keyboard navigable, WCAG AA

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn |
| ORM / Migrations | SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL on Neon (JSONB for parsed data) |
| Validation / Config | Pydantic v2, pydantic-settings |
| **Auth** | **JWT access + refresh tokens (PyJWT), password hashing via argon2-cffi (Argon2id); roles `admin`, `recruiter`** |
| Rate limiting | slowapi |
| PDF parsing | pdfplumber, fallback PyMuPDF |
| DOCX parsing | python-docx |
| NLP | spaCy `en_core_web_sm`, rapidfuzz |
| Classical ML | scikit-learn (TF-IDF cosine similarity) |
| Frontend | React 18 + Vite + JavaScript (JSX) |
| Styling | Tailwind CSS v3, shadcn/ui |
| State | TanStack Query, React Router v6 |
| Forms / Tables | React Hook Form, TanStack Table |
| Charts | Recharts |
| HTTP | Axios |
| Toasts | sonner |

> **Auth note:** `passlib` was intentionally replaced with `argon2-cffi`. Python 3.13+ removed the `crypt` standard library module that passlib depended on for some backends, and passlib is no longer actively maintained. `argon2-cffi` is actively maintained and provides the Argon2id algorithm directly, which is the current OWASP-recommended password hashing algorithm.

---

## Architecture

```
Recruiter (browser)
   |
   v
React + Vite frontend  (localhost:5173)
   |  JSON REST  /api/v1
   v
FastAPI backend  (localhost:8000)
   |-- core/       config, security, logging, rate limit, errors
   |-- api/v1/     thin routes -> services -> schemas
   |-- services/   parsing, matching, storage, analytics, export
   |-- tasks/      background parse + score
   |-- models/     SQLAlchemy ORM
   v
PostgreSQL (Neon)    +   backend/storage/resumes/  (private, UUID-named)
```

See `docs/architecture.md` for the full diagram and data-flow description.

---

## Prerequisites

- Python 3.14
- Node 20+
- Git
- A free [Neon](https://neon.tech) PostgreSQL database (connection string required)

---

## Quick Start (Windows PowerShell)

### Backend

```powershell
# From the repo root
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # if blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Create your .env from the example, then add your Neon connection string
copy .env.example .env              # edit DATABASE_URL and JWT_SECRET

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/api/v1/health

### Frontend

```powershell
# In a second terminal, from the repo root
cd frontend
npm install                         # or npm.cmd if 'npm' fails on Windows PowerShell
copy .env.example .env              # edit VITE_API_URL if needed
npm run dev                         # http://localhost:5173 (or npm.cmd run dev)
```

> **Windows PowerShell note:** If `npm` commands are blocked or fail to resolve in PowerShell, use `npm.cmd` instead (e.g. `npm.cmd install`, `npm.cmd run dev`).

---

## API Documentation

Interactive Swagger UI: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

---

## Known Limitations

- **No OCR** — scanned or image-only PDFs are marked `failed` with reason `scanned_or_empty`
- **Status is per-candidate, not per-job** — a candidate appearing in two jobs shares one pipeline status
- **Keyword + similarity scoring** can miss unusual or highly creative phrasing
- **No measured accuracy** — no precision/recall figures are claimed without an evaluation dataset
- **Background tasks run in-process** — no persistent queue; a restart during parsing marks affected resumes as `failed` with reason `interrupted` (recovered on next startup)
- **Single-user ownership model** — no team workspaces; each job/resume is owned by one recruiter account
