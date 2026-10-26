# HireLens: AI Resume Screening and Candidate Ranking Platform

**Project plan and agent specification (v2, merged edition)**

> **Scope note: this is a college minor project.** It runs locally: frontend and backend on the developer's Windows machine, database on Neon. Automated tests, CI/CD, Docker images and cloud deployment are **OUT OF SCOPE** until after submission. Do not create test files, GitHub Actions workflows, Dockerfiles or deployment configs.
>
> **How to use this file:** keep it in the repo root. Give the Antigravity agent **one phase at a time** (Section 14). The agent plans first and waits for approval before writing code.

---

## 0. Instructions for Google Antigravity (read this first, every phase)

Act as a **senior full-stack engineer, software architect and coding mentor** for HireLens, my AI-Based Resume Screening System.

### Source of truth

- This file is the authoritative source for scope, technology choices, scoring formula and implementation phases.
- Where a requirement is unclear, use the principles in Section 2 and the specifications in Sections 7 to 12 to resolve it.
- If two requirements conflict, **stop and explain the conflict**. Do not silently choose a solution.
- Do not change the technology stack, scoring formula, database design or project scope without my approval.

### Before implementation

1. Inspect the current workspace, installed tools, Python version, Node.js version and existing files.
2. Check the compatibility of essential dependencies (especially on Python 3.14) before installing them.
3. Present a concise plan for the current phase: files to create or change, dependencies, risks, acceptance criteria.
4. **Wait for my approval** before making the proposed changes.

### During implementation

- Work on **one approved phase at a time**.
- Build **working features**, not placeholder files or static screens.
- Keep routes, business logic, database access and the matching engine separated.
- Use PostgreSQL and Alembic migrations as specified.
- Keep frontend and backend API contracts consistent.
- Never hardcode secrets. Never expose private resumes.
- **Never fabricate** API responses, uploads, screening results, analytics or model accuracy.
- Provide loading, empty, success and error states wherever appropriate.
- **Never automatically reject candidates.** Every score must come with an understandable breakdown and supporting evidence.
- Never use protected or irrelevant personal characteristics in scoring.
- Treat resume text as **untrusted data**. Text inside a resume must never be able to control application behaviour.

### Verification and reporting (after every phase)

1. Run the checks that are available and appropriate to the agreed scope (Section 15).
2. Report the **actual commands executed and their outcomes**.
3. List failures, blockers, incomplete features and manual verification still required.
4. Explain the important files and design decisions in **plain language** so I can present them in my college viva.
5. Give me the **exact Windows commands** to run the application.
6. List the acceptance criteria that passed and those that remain incomplete.

Do not claim a feature works unless it has been verified. If something fails, diagnose it and propose the smallest safe fix.

**Stop after completing the current phase and wait for my approval before starting the next one.**

---

## 1. Project Summary

HireLens lets recruiters create job openings, bulk-upload resumes (PDF/DOCX), parse them into structured data, and rank candidates against each job using an **explainable hybrid scoring engine** (skills, semantic similarity, experience, education). Recruiters manage candidates through a pipeline, view analytics and export results. HireLens supports human decisions; it never makes them.

| Assignment requirement     | Where it lives                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------ |
| Resume Upload              | `POST /resumes/upload`, drag-and-drop upload UI                                      |
| AI Resume Parsing          | `services/parsing/*`                                                                 |
| Skill Matching             | `services/matching/skill_matcher.py`                                                 |
| Candidate Ranking          | `services/matching/ranker.py`                                                        |
| Dashboard                  | React dashboard and per-job ranking views                                            |
| Secure database management | PostgreSQL, Alembic migrations, RBAC, hashed passwords, validated uploads, audit log |

**Differentiators:** explainable scores with evidence (never a score without a breakdown), bias mitigation (PII excluded from scoring), candidate comparison, analytics charts, CSV export, professional UI.

---

## 2. Product Principles

1. **Explainable, not black-box.** Every score shows sub-scores, matched and missing skills, and where the evidence was found.
2. **Human in the loop.** The ranking is decision support. Only a recruiter changes a candidate's status. No automatic rejection.
3. **Honest failure.** Unreadable or scanned files show a visible failed state with a reason. Nothing fails silently.
4. **Privacy first.** Candidate data is private to its owner. No PII in logs.
5. **No fake data.** Demo data is clearly synthetic. Dashboards show persisted data only.
6. **No unsupported claims.** Accuracy is never claimed without evaluation evidence.
7. **Modular and maintainable.** Thin routes, services hold the logic, the matching engine runs independently of HTTP.
8. **Consistent and accessible UI.** Keyboard navigable, readable in light and dark mode.

---

## 3. Ground Rules for the AI Agent

1. **Routes stay thin.** Business logic lives in `services/`. Routes validate input, call a service, return a schema.
2. **Backend:** Python with type hints. **Frontend:** plain JavaScript (JSX), **NOT TypeScript**. ES modules, functional components, hooks, short JSDoc on non-obvious functions.
3. Config via environment variables (`pydantic-settings`). Never hardcode secrets. Never commit `.env`.
4. Database changes **only** through Alembic migrations.
5. **Never trust uploads.** Validate size, real file type (magic bytes) and extension. Rename to UUID. Store outside any public directory.
6. **Never return a match score without its explanation object.**
7. Do not use name, gender, age, photo or address in scoring.
8. Do not log resume contents or PII. Log IDs only.
9. Small, meaningful commits with conventional messages (`feat:`, `fix:`, `docs:`, `chore:`).
10. Every UI screen has loading (skeleton), empty and error states.
11. **Do not add dependencies that are not listed in this plan without asking first.**
12. Do NOT write tests, CI workflows, Dockerfiles or deployment config (out of scope for now).
13. After each phase, give a short "how to run and check this phase" note and explain the key files in plain language for the viva.
14. Never replace PostgreSQL with SQLite, and never replace React with Streamlit or any other framework.
15. Never leave major features as TODOs while reporting the phase as complete.
16. Never overwrite existing user files without inspecting them first.
17. Do not suppress errors, and do not use broad `except Exception: pass`. Handle or surface every error.

### Environment (Windows)

- Windows. Python **3.14** is the default `python` command. Create the virtualenv with `python -m venv .venv` inside `backend/`.
- Use Windows-compatible commands only: no `make`, no bash-only syntax. Prefer PowerShell. Use `curl.exe` (not the `curl` alias) or Swagger UI for API checks.
- Use `python-magic-bin` instead of `python-magic`.
- Install the **latest** versions of libraries (older releases may lack Python 3.14 wheels).
- **If any package fails to install on Python 3.14, STOP and tell me the package name and the error.** Do not silently downgrade Python, pin old versions, or swap libraries.
- Known risk areas to check first in Phase 0: `spacy` (and its model), `sentence-transformers` (needs PyTorch), `scikit-learn`, `PyMuPDF`, `passlib` (lightly maintained; if it breaks, propose `argon2-cffi` directly and ask me).

---

## 4. Tech Stack (approved)

### Backend

| Concern               | Choice                                                                                                           |
| --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Language / framework  | Python 3.14, FastAPI                                                                                             |
| ORM / migrations      | SQLAlchemy 2.0 + Alembic                                                                                         |
| Database              | PostgreSQL on Neon (hosted free tier; JSONB for parsed data)                                                     |
| Validation / settings | Pydantic v2, pydantic-settings                                                                                   |
| Auth                  | JWT access + refresh tokens (PyJWT), password hashing via argon2-cffi (Argon2id); roles `admin`, `recruiter` |
| Rate limiting         | slowapi (login and upload)                                                                                       |
| File type check       | python-magic-bin                                                                                                 |
| PDF text              | pdfplumber, fallback PyMuPDF                                                                                     |
| DOCX text             | python-docx                                                                                                      |
| NLP                   | spaCy (`en_core_web_sm`) with PhraseMatcher                                                                      |
| Fuzzy matching        | rapidfuzz                                                                                                        |
| Classical ML          | scikit-learn (TF-IDF + cosine similarity)                                                                        |
| Semantic model        | sentence-transformers (`all-MiniLM-L6-v2`), optional via `EMBEDDINGS_ENABLED`                                    |
| Background work       | FastAPI `BackgroundTasks`                                                                                        |
| Code quality          | ruff                                                                                                             |

### Frontend

| Concern      | Choice                                 |
| ------------ | -------------------------------------- |
| Framework    | React 18 + Vite + **JavaScript (JSX)** |
| Styling      | Tailwind CSS + shadcn/ui (JS config)   |
| Icons        | lucide-react                           |
| Routing      | React Router v6                        |
| Server state | TanStack Query                         |
| Tables       | TanStack Table                         |
| Forms        | React Hook Form (+ Zod, optional)      |
| Charts       | Recharts                               |
| HTTP         | Axios with token-refresh interceptor   |
| Toasts       | sonner                                 |
| Code quality | ESLint, Prettier                       |

### Local dev tooling

Python 3.14 virtualenv, Node 20+, Git, and a Neon Postgres database (connection string in `backend/.env`). **No Docker.**

---

## 5. System Architecture

A **modular monolith**: one FastAPI backend, one React frontend, one database.

```
Recruiter (browser)
   |
   v
React + Vite frontend (localhost:5173)
   |  HTTPS/JSON REST  (/api/v1)
   v
FastAPI backend (localhost:8000)
   |-- core/        config, security, logging, rate limit, errors
   |-- api/v1/      thin routes -> call services -> return schemas
   |-- services/
   |     |-- parsing/    text -> sections -> contact -> skills -> experience -> education
   |     |-- matching/   skill + semantic + experience + education -> score -> explanation -> rank
   |     |-- storage / upload validator / analytics / export
   |-- tasks/       background parse + score
   |-- models/      SQLAlchemy models
   v
PostgreSQL (Neon)         Private file storage (backend/storage/resumes, UUID names)
```

**Data flow:** upload -> validate -> store file (UUID name) -> create `Resume` (pending) -> background task parses -> `ParsedResume` saved (done/failed) -> match job to resume -> `MatchResult` with breakdown -> ranking endpoint reads results.

The **matching engine** (`services/matching/`) must be pure Python functions that take plain data in and return plain data out, with no HTTP or database imports inside the scoring functions.

---

## 6. Repository Structure

```
hirelens/
|-- PROJECT_PLAN.md
|-- README.md
|-- LICENSE                      # MIT
|-- .gitignore
|
|-- docs/
|   |-- architecture.md          # diagram + data flow
|   |-- scoring.md               # formula, weights, rescaling, bias mitigation, examples
|   |-- database.md              # ER diagram + table descriptions
|   |-- security.md              # security controls summary
|   `-- screenshots/
|
|-- backend/
|   |-- .env.example             # backend env template (real .env is git-ignored)
|   |-- requirements.txt
|   |-- alembic.ini
|   |-- alembic/ (env.py, versions/)
|   |-- data/
|   |   |-- skills_taxonomy.json # 300-500 skills: canonical, aliases, category
|   |   `-- degree_levels.json
|   |-- scripts/
|   |   |-- seed_demo.py         # demo users, jobs, sample candidates
|   |   `-- download_models.py   # spaCy / transformer model download
|   |-- sample_resumes/          # synthetic demo resumes ONLY
|   |-- storage/                 # uploaded files (git-ignored, never served statically)
|   `-- app/
|       |-- main.py              # app factory, middleware, routers
|       |-- core/                # config, security, logging (PII-safe), rate_limit, exceptions
|       |-- db/                  # base.py, session.py
|       |-- models/              # user, job (Job, JobRequirement), candidate,
|       |                        # resume (Resume, ParsedResume), match_result, audit_log,
|       |                        # app_setting
|       |-- schemas/             # auth, user, job, candidate, resume, match (ScoreBreakdown), analytics
|       |-- api/
|       |   |-- deps.py          # get_current_user, require_role, pagination
|       |   `-- v1/              # router, auth, users, jobs, candidates, resumes,
|       |                        # matching, analytics, settings, health
|       |-- services/
|       |   |-- auth_service.py, job_service.py, candidate_service.py
|       |   |-- storage_service.py, upload_validator.py
|       |   |-- parsing/         # text_extractor, section_splitter, contact_extractor,
|       |   |                    # skill_extractor, experience_parser, education_parser, pipeline
|       |   |-- matching/        # skill_matcher, semantic_matcher, experience_matcher,
|       |   |                    # education_matcher, scorer, explainer, ranker
|       |   |-- analytics_service.py, export_service.py
|       |-- tasks/processing.py  # background parse + score
|       `-- utils/               # text_cleaning.py, csv_sanitize.py
|
`-- frontend/
    |-- .env.example             # VITE_API_URL
    |-- package.json, vite.config.js, jsconfig.json (@/ alias)
    |-- tailwind.config.js, postcss.config.js, components.json, index.html
    |-- public/
    `-- src/
        |-- main.jsx, App.jsx, routes.jsx
        |-- lib/        # api.js, queryClient.js, utils.js, constants.js
        |-- hooks/      # useAuth, useJobs, useCandidates, useRanking, useAnalytics
        |-- context/    # AuthContext.jsx, ThemeContext.jsx
        |-- components/
        |   |-- ui/         # shadcn primitives
        |   |-- layout/     # AppShell, Sidebar, Topbar, PageHeader
        |   |-- common/     # EmptyState, ErrorState, SkeletonTable, ConfirmDialog, StatCard
        |   |-- jobs/       # JobForm, JobCard, RequirementEditor
        |   |-- resumes/    # UploadDropzone, ParseStatusBadge
        |   |-- candidates/ # RankingTable, ScoreRing, ScoreBreakdownPanel, SkillChips,
        |   |               # CandidateDrawer, CompareView, StatusSelect
        |   `-- charts/     # ScoreDistributionChart, TopSkillsChart, PipelineFunnelChart
        `-- pages/      # Login, Register, Dashboard, Jobs, JobCreate, JobDetail,
                        # Candidates, CandidateDetail, Settings, NotFound
```

---

## 7. Database Design

All tables use UUID primary keys and `created_at` / `updated_at`. Index every foreign key and `match_results.total_score`.

| Table                                                  | Key columns                                                                                                                                                                         |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `users`                                                | id, email (unique), hashed_password, full_name, role (`admin`/`recruiter`), is_active                                                                                               |
| `jobs`                                                 | id, owner_id -> users, title, description, department, location, min_experience_years, education_level, status (`open`/`closed`), weights_override (JSONB, nullable)                |
| `job_requirements`                                     | id, job_id, skill (canonical), importance (`required`/`preferred`), weight                                                                                                          |
| `candidates`                                           | id, owner_id, full_name, email, phone, links (JSONB), status (`new`/`screened`/`shortlisted`/`interview`/`rejected`), notes                                                         |
| `resumes`                                              | id, candidate_id, job_id (nullable), original_filename, stored_filename (UUID), mime_type, size_bytes, sha256, parse_status (`pending`/`processing`/`done`/`failed`), parse_error   |
| `parsed_resumes`                                       | id, resume_id (unique), raw_text, skills (JSONB, with evidence), experience (JSONB), education (JSONB), total_experience_years, highest_degree, sections (JSONB), parser_version    |
| `match_results`                                        | id, job_id, candidate_id, resume_id, total_score, skill_score, semantic_score, experience_score, education_score, breakdown (JSONB), scoring_version; **unique(job_id, resume_id)** |
| `audit_logs`                                           | id, user_id, action, entity_type, entity_id, metadata (JSONB, no PII), created_at                                                                                                   |
| `app_settings` _(addition, needs approval in Phase 1)_ | key (unique), value (JSONB), updated_by. Stores the global scoring weights so the admin Settings sliders persist. Env weights are the defaults.                                     |

**Design notes**

- Keep `raw_text` and parsed JSON so resumes can be **re-scored without re-parsing** when weights change.
- Store the file `sha256` to detect duplicate uploads (warn the recruiter, do not silently drop).
- Deleting a candidate deletes their files, parsed data and match results.
- `parsed_resumes.skills` stores **evidence**, not just names (see 9.1 step 6).
- **Known limitation (documented, not fixed in v1):** candidate `status` is per candidate, not per job. A candidate in two jobs shares one status.

---

## 8. API Design (`/api/v1`)

- **Auth:** `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
- **Jobs:** `POST /jobs`, `GET /jobs` (pagination + search), `GET /jobs/{id}`, `PUT /jobs/{id}`, `DELETE /jobs/{id}`, `POST /jobs/{id}/extract-requirements`
- **Resumes:** `POST /resumes/upload` (multi-file, optional `job_id`), `GET /resumes/{id}`, `GET /resumes/{id}/status`, `GET /resumes/{id}/file` (authenticated), `DELETE /resumes/{id}`
- **Candidates:** `GET /candidates`, `GET /candidates/{id}`, `PATCH /candidates/{id}` (status, notes), `DELETE /candidates/{id}`
- **Matching:** `POST /jobs/{id}/match`, `GET /jobs/{id}/ranking?min_score=&skill=&min_exp=&status=&page=`, `GET /jobs/{id}/candidates/{candidate_id}/match`, `GET /jobs/{id}/export.csv`
- **Analytics:** `GET /analytics/overview`, `GET /jobs/{id}/analytics`
- **Settings (admin):** `GET /settings/weights`, `PUT /settings/weights`, `POST /settings/rescore-all`
- **Ops:** `GET /health` (also reports database connectivity)

**Conventions**

- Error shape: `{ "error": { "code", "message", "details" } }`
- Pagination: `{ items, total, page, page_size }`
- Every list is **scoped to the current user's data** (IDOR-safe). Requesting another user's ID returns 404, not 403.
- Any endpoint returning a match includes the full `ScoreBreakdown`.

---

## 9. Parsing and Scoring Specification

### 9.1 Parsing pipeline

1. **Validate** the file: size <= 5 MB, extension `pdf`/`docx`, magic bytes match, not empty.
2. **Extract text:** `pdfplumber`, fallback `PyMuPDF`; `python-docx` for DOCX. If almost no text, mark `failed` with reason `scanned_or_empty` (OCR is out of scope).
3. **Clean text:** whitespace, ligatures, bullets, hyphenated line breaks.
4. **Split sections** via fuzzy heading detection (Summary, Experience, Education, Skills, Projects, Certifications).
5. **Extract contact info:** regex for email/phone/links; spaCy `PERSON` + first-lines heuristic for name.
6. **Extract skills:** taxonomy + `PhraseMatcher` + `rapidfuzz`; map aliases to canonical names (e.g. `js` -> `JavaScript`). For every skill record **evidence**: `{skill, found_in_section, match_type: exact|alias|fuzzy, snippet}`. Snippets are short (<= 120 characters), taken from de-identified text, and never logged. Fuzzy matching uses a high threshold and is skipped for short tokens so that "Java" is never matched to "JavaScript".
7. **Parse experience** (date ranges -> months, merge overlapping ranges, handle "Present") and **education** (degree level, field).
8. **Save** `ParsedResume`, set `parse_status = done`. On any exception set `failed` with a safe `parse_error` code (no resume content in the message).

**Background processing:** use `BackgroundTasks`. On app startup, mark any resume stuck in `processing` for more than 10 minutes as `failed` with reason `interrupted`, so a server restart never leaves a permanent spinner.

### 9.2 Scoring

Weights live in config and can be overridden per job (must sum to 1.0, validated):

```
total = 0.40 * skill_score
      + 0.30 * semantic_score
      + 0.20 * experience_score
      + 0.10 * education_score        # each sub-score normalized to 0-100
```

| Sub-score            | Rule                                                                                                                                                                                                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **skill_score**      | `required` skills weigh 2x `preferred`; `matched_weight / total_weight * 100`.                                                                                                                                                                                                                                      |
| **semantic_score**   | Cosine similarity of job description vs. de-identified resume text. TF-IDF by default; embeddings when `EMBEDDINGS_ENABLED=true`. Raw TF-IDF cosine is usually low, so the agent must propose a documented, monotonic rescaling to 0-100 in its Phase 3 plan and get my approval. Document it in `docs/scoring.md`. |
| **experience_score** | 100 if candidate years >= required, scaled down proportionally below it. Years come from merged date ranges.                                                                                                                                                                                                        |
| **education_score**  | Highest degree level vs. requirement using `degree_levels.json` (100 if met or exceeded, scaled down below it).                                                                                                                                                                                                     |

**Missing component handling:** if a job has no requirements, no minimum experience or no education level, that component is **not silently scored as 0 or 100**. The remaining weights are re-normalized proportionally and a note is added to the explanation (for example "No required skills defined, so skill score was excluded"). Components that did not contribute are marked `null` in the breakdown.

**Explanation object (always returned):**

```json
{
  "total_score": 78.4,
  "sub_scores": {
    "skills": 82,
    "semantic": 71,
    "experience": 90,
    "education": 100
  },
  "weights_used": {
    "skills": 0.4,
    "semantic": 0.3,
    "experience": 0.2,
    "education": 0.1
  },
  "matched_skills": [
    {
      "skill": "Python",
      "importance": "required",
      "found_in": "experience",
      "match_type": "exact",
      "snippet": "Built REST APIs in Python and Flask"
    },
    {
      "skill": "SQL",
      "importance": "required",
      "found_in": "skills",
      "match_type": "alias",
      "snippet": "PostgreSQL, SQL"
    }
  ],
  "missing_required": ["Docker"],
  "missing_preferred": ["Kubernetes"],
  "extra_skills": ["Tableau"],
  "experience": { "candidate_years": 3.5, "required_years": 3 },
  "education": { "candidate_level": "bachelor", "required_level": "bachelor" },
  "notes": ["Docker is a required skill and was not found in the resume"],
  "scoring_version": "1.0.0"
}
```

Changing weights or the formula bumps `scoring_version`. Old results remain explainable by the version that produced them.

### 9.3 Bias mitigation and responsible use

- Scoring functions receive **only** skills, experience, education level and **de-identified text** (name and contact details stripped). Photos and addresses are never parsed into scoring inputs.
- Name, gender, age, photo, address and other personal attributes never enter a scoring function. Document this in `docs/scoring.md`.
- The UI shows a short notice that scores are decision support and that every decision stays with the recruiter.
- Bulk reject always opens a confirm dialog. Nothing is auto-rejected.
- `docs/scoring.md` states the limitations honestly: keyword and similarity matching can miss unusual phrasing, and no accuracy figure is claimed without an evaluation.

---

## 10. Security Requirements

| Area              | Control                                                                                                                                                                    |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Passwords         | argon2/bcrypt hashing, minimum length policy (>= 8)                                                                                                                        |
| Registration      | Public registration creates `recruiter` only. `admin` is created through the seed script.                                                                                  |
| Tokens            | Short-lived access JWT, refresh token, secret from env                                                                                                                     |
| Access control    | `require_role` dependency; every query filtered by owner; IDOR-safe                                                                                                        |
| Uploads           | Size cap, magic-byte check, extension allow-list, UUID filenames, stored outside static dirs, served only through an authenticated endpoint, duplicate detection by sha256 |
| Untrusted content | Resume text is data only. It is never executed, never rendered as HTML (React escapes it), never used to build commands or queries.                                        |
| Rate limiting     | Stricter limits on `/auth/login` and `/resumes/upload`                                                                                                                     |
| Input             | Pydantic validation; ORM only, no string-built SQL                                                                                                                         |
| CSV export        | Sanitize cells starting with `=`, `+`, `-`, `@` (formula injection)                                                                                                        |
| Headers / CORS    | CORS allow-list from `FRONTEND_ORIGIN`, security headers                                                                                                                   |
| Privacy           | No PII in logs, deletion cascades to files, audit log for sensitive actions (login, register, upload, delete, status change, weight change, export)                        |
| Demo account      | The "Try demo account" button appears only when `ENVIRONMENT=development` and demo data is seeded                                                                          |

---

## 11. UI / UX Specification

### 11.1 Design system

- **Style:** clean SaaS dashboard (Linear / Vercel / Stripe feel): generous whitespace, subtle borders, soft shadows, `rounded-lg`.
- **Fonts:** Inter (UI), JetBrains Mono (IDs/code).
- **Colors:** primary indigo (`#4F46E5` range); slate neutrals; green = matched/good, amber = partial, red = missing/rejected, blue = info. Score colors: >= 75 green, 50-74 amber, < 50 red.
- **Dark mode:** toggle in topbar, persisted, built on CSS variables.
- **Type scale:** page title 24px semibold, section title 16px medium, body 14px. 4px spacing grid.
- **Motion:** subtle 150-200ms transitions only.
- **Accessibility:** keyboard navigable, visible focus rings, ARIA labels, **never color-only signals** (always pair color with text or icon), WCAG AA contrast.
- **Responsive:** great at 1280px+, tablet-friendly, sidebar collapses on small screens.

### 11.2 Layout

Collapsible left sidebar (Dashboard, Jobs, Candidates, Settings), topbar (global search, theme toggle, user menu), centered content (max ~1400px) with a `PageHeader` (title, breadcrumbs, primary action).

### 11.3 Screens

1. **Login / Register:** split layout (brand panel + form), inline validation, "Try demo account" button (development only).
2. **Dashboard:** four `StatCard`s (open jobs, candidates, resumes processed, avg match score), recent activity, pipeline funnel chart, score distribution chart, quick actions. All numbers come from the database.
3. **Jobs list:** searchable/filterable table or card grid, status badges, applicant counts, top-score preview.
4. **Create / Edit job:** title, description, location, experience, education, plus `RequirementEditor` (skill chips with required/preferred toggle) and a **"Suggest skills from description"** button.
5. **Job detail (tabs):**
   - _Overview:_ summary, requirements, stats.
   - _Candidates:_ drag-and-drop upload zone (per-file progress and parse status) above the **ranking table** (rank, candidate, `ScoreRing`, top matched skills, missing required skills, experience, status), with filters (min score slider, skill, experience, status), sorting, pagination, bulk shortlist/reject (with confirm), CSV export, and the decision-support notice.
   - _Analytics:_ score distribution, common skills, common skill gaps.
6. **Candidate drawer:** contact info, `ScoreBreakdownPanel` (sub-score bars with weights), `SkillChips` (matched green, missing red, extra gray, each with an icon so color is not the only signal), evidence snippets, experience timeline, education, original file download, status and notes, **Compare** action.
7. **Compare view:** 2-3 candidates side by side with a skill matrix.
8. **Settings:** profile, theme, and (admin) scoring weight sliders summing to 100 with a "Re-score all" action (with confirm).
9. **System states:** skeleton loaders, friendly empty states with a call to action, error states with retry, toasts, confirm dialogs for destructive actions, 404 page.

### 11.4 UI quality checklist

- [ ] Consistent spacing; no raw unstyled HTML elements
- [ ] Light and dark mode both polished
- [ ] Every data view has loading, empty and error states
- [ ] Tables sortable, paginated, keyboard accessible
- [ ] No layout shift when data loads
- [ ] Color is never the only signal
- [ ] No console errors in the browser

---

## 12. Environment Variables

`backend/.env.example`:

```
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
FRONTEND_ORIGIN=http://localhost:5173

# Neon connection string. Keep ?sslmode=require.
# Use the DIRECT (non-pooled) host for Alembic migrations.
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require

JWT_SECRET=change-me-use-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

UPLOAD_DIR=./storage/resumes
MAX_UPLOAD_MB=5
MAX_FILES_PER_BATCH=20

EMBEDDINGS_ENABLED=false
WEIGHT_SKILLS=0.40
WEIGHT_SEMANTIC=0.30
WEIGHT_EXPERIENCE=0.20
WEIGHT_EDUCATION=0.10
```

`frontend/.env.example`:

```
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 13. Windows Run Commands (reference)

PowerShell, from the repo root:

```powershell
# Backend (first time)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install -r requirements.txt
python -m spacy download en_core_web_sm
copy .env.example .env                 # then edit .env with your Neon string
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
copy .env.example .env
npm run dev                            # http://localhost:5173
```

API docs: `http://localhost:8000/docs`. Health: `http://localhost:8000/api/v1/health`.

The agent must keep these commands accurate in the README as the project evolves.

---

## 14. Build Phases (give to the agent one at a time)

For **every** phase the agent follows Section 0: inspect, propose a plan, **wait for approval**, implement, verify, report, **stop**.

### Phase 0: Scaffold and dependency check

**Prompt:** "Read PROJECT_PLAN.md fully. Do Phase 0 only. First inspect my workspace, Python and Node versions, and check that every dependency in Section 4 installs on Python 3.14; report any that do not, with the exact error. Then present your plan and wait for approval. After approval: create the repo skeleton from Section 6 (empty modules with short docstrings; skip anything related to tests, CI, Docker or deployment), add `.env.example` files and `.gitignore`, a FastAPI app with `/api/v1/health` that also checks the Neon database connection, and a Vite + React JavaScript (JSX, not TypeScript) app with Tailwind and shadcn/ui initialized (JS config) rendering a placeholder page. Put the exact Windows run commands in the README. No feature code yet."

**Acceptance criteria**

- [ ] Dependency compatibility report delivered (installs on 3.14, or blockers named)
- [ ] Backend runs on port 8000; `/api/v1/health` reports the database as connected
- [ ] Frontend runs on port 5173 and renders the placeholder
- [ ] `.env` is git-ignored; `.env.example` files exist
- [ ] `ruff check` and `npm run lint` pass

### Phase 1: Database and Auth

**Prompt:** "Do Phase 1 only. Implement the SQLAlchemy models, the Alembic initial migration, and auth (register, login, refresh, me) with role-based dependencies, per Sections 7, 8 and 10. Include the `app_settings` table if I approve it in your plan."

**Acceptance criteria**

- [ ] Migration applies cleanly on Neon (`alembic upgrade head`, `alembic current` shows head)
- [ ] Register and login work in Swagger UI; passwords are stored hashed
- [ ] Refresh token flow works
- [ ] A protected route rejects unauthenticated requests (401)
- [ ] `require_role` blocks a recruiter from an admin-only route (403)
- [ ] Public registration cannot create an admin
- [ ] Rate limit on `/auth/login` works

### Phase 2: Jobs, Upload and Parsing

**Prompt:** "Do Phase 2 only. Implement jobs CRUD, the upload validator and storage service, the full parsing pipeline (Section 9.1) including skill evidence, `skills_taxonomy.json` with 300+ skills and aliases, `degree_levels.json`, and the extract-requirements endpoint. Run parsing as a background task and expose `parse_status`. Add startup recovery for stuck `processing` resumes."

**Acceptance criteria**

- [ ] Jobs CRUD works and is scoped to the owner (another user's job returns 404)
- [ ] Uploading a synthetic PDF and DOCX produces structured parsed data (skills with evidence, experience, education, contact)
- [ ] Oversized, fake-extension, wrong-magic-bytes and empty files are rejected with the standard error shape
- [ ] A scanned/blank PDF ends as `failed` with `scanned_or_empty`
- [ ] Stored filenames are UUIDs, files are not reachable through any static URL, `/resumes/{id}/file` requires auth
- [ ] Duplicate upload (same sha256) is detected and reported
- [ ] Logs contain IDs only, no resume text

### Phase 3: Matching and Ranking

**Prompt:** "Do Phase 3 only. Implement the scoring engine, explainer and ranker per Section 9.2 with config-driven weights, missing-component handling, the matching/ranking/export endpoints, re-scoring without re-parsing, and CSV sanitization. In your plan, propose the TF-IDF rescaling for my approval. Write `docs/scoring.md`."

**Acceptance criteria**

- [ ] `GET /jobs/{id}/ranking` returns sorted candidates, **each with a full breakdown**
- [ ] Every match response contains the explanation object (no bare scores anywhere)
- [ ] Changing weights and re-scoring updates results without re-parsing; `scoring_version` bumps
- [ ] A job with no requirements produces re-normalized weights and a note, not a fake score
- [ ] Filters (`min_score`, `skill`, `min_exp`, `status`) and pagination work
- [ ] CSV export opens correctly and cells starting with `= + - @` are neutralized
- [ ] Scoring functions import nothing from the web or database layers and receive no PII fields
- [ ] A small hand-checked example in `docs/scoring.md` matches the engine's output

### Phase 4: Frontend foundation and core screens (vertical slice)

**Prompt:** "Do Phase 4 only. Set up the design tokens from Section 11.1, AppShell, auth flow, API client with token refresh, and build Login, Register, Jobs list, Create Job, and Job Detail with the upload dropzone and ranking table. Follow the UI quality checklist. Connect everything to the real backend."

**Acceptance criteria**

- [ ] I can log in, create a job, upload resumes, watch parse status update, and see a ranked list from real data
- [ ] Expired access token refreshes transparently; a failed refresh sends me to login
- [ ] Loading, empty and error states exist on every screen built
- [ ] Layout works at 1280px and on a tablet width
- [ ] `npm run lint` and `npm run build` pass; no console errors
- [ ] Work is committed and tagged (for example `v0.4-vertical-slice`)

### Phase 5: Advanced UI

**Prompt:** "Do Phase 5 only. Build the Dashboard with charts, the candidate drawer with ScoreBreakdownPanel and SkillChips (with evidence), Compare view, status management, filters, bulk actions with confirmation, the Settings page with weight sliders and Re-score all, dark mode, and all empty/loading/error states."

**Acceptance criteria**

- [ ] Section 11.4 checklist passes in both light and dark mode
- [ ] Dashboard numbers match the database (spot-check against Swagger responses)
- [ ] Drawer shows sub-score bars with weights, evidence, and a working file download
- [ ] Compare view shows 2-3 candidates with a skill matrix
- [ ] Weight sliders force a sum of 100 and re-scoring updates the ranking
- [ ] Bulk reject requires confirmation; nothing is auto-rejected anywhere
- [ ] Keyboard-only navigation works on tables, dialogs and the drawer

### Phase 6: Hardening and Docs

**Prompt:** "Do Phase 6 only. Add security headers and audit logging, finish rate limiting, create `seed_demo.py` with synthetic demo data (including the admin account), and write the README (features, architecture diagram, setup steps, tech decisions, screenshot placeholders, security notes, limitations) and the docs in `docs/`."

**Acceptance criteria**

- [ ] A fresh clone can be set up from the README alone and shows demo data after seeding
- [ ] Audit log records the actions listed in Section 10
- [ ] Security headers present on responses; CORS limited to `FRONTEND_ORIGIN`
- [ ] No secrets, real resumes or `.env` in the repository (`git log` and `git status` checked)
- [ ] `docs/architecture.md`, `scoring.md`, `database.md`, `security.md` complete
- [ ] README lists known limitations (see Section 17)

---

## 15. Verification Without Automated Tests

Automated tests are out of scope, but "verified" still means evidence. After each phase the agent runs what applies and reports the real output:

| Check                  | Command (PowerShell)                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| Python lint            | `ruff check .` (from `backend/`)                                                         |
| App imports and starts | `uvicorn app.main:app --port 8000` then open `/docs`                                     |
| Migrations             | `alembic upgrade head` and `alembic current`                                             |
| API smoke checks       | Swagger UI, or `curl.exe http://localhost:8000/api/v1/health`                            |
| Frontend lint          | `npm run lint`                                                                           |
| Frontend build         | `npm run build`                                                                          |
| UI check               | Run the app in the browser and exercise the phase's screens, including the failure paths |

Manual steps the agent cannot do itself (for example "upload a corrupted PDF in the browser") go in the report under **manual verification still required**.

---

## 16. End-of-Phase Report Template

The agent ends every phase with exactly this structure:

1. **Phase and status** (complete / partially complete / blocked)
2. **Files created or modified**
3. **Features completed**
4. **Commands executed and their actual outcomes**
5. **Acceptance criteria:** passed / not passed
6. **Failures, blockers, known limitations**
7. **Manual verification still required**
8. **Plain-language explanation of the key files and design decisions** (viva notes)
9. **Exact Windows commands to run the app**
10. **Proposed next step.** Then stop and wait for my approval.

---

## 17. Definition of Done (for submission)

- [ ] All six assignment requirements demonstrably work locally
- [ ] Every score shows its breakdown and evidence; no score appears without one
- [ ] No candidate is ever auto-rejected; all status changes are recruiter actions
- [ ] Parsing failures show clear, visible reasons
- [ ] Setup works from the README on a fresh clone
- [ ] No secrets or real resumes in the repo
- [ ] README has an architecture diagram, screenshots and limitations
- [ ] Dashboard figures reflect actual persisted data
- [ ] I can explain every module without looking at the code

**Known limitations to state in the README:** no OCR for scanned PDFs; status is per candidate rather than per job; keyword and similarity scoring can miss unusual phrasing; no measured accuracy yet; background tasks run in-process (no queue); single-user ownership model (no team workspaces).

---

## 18. Viva Cheat Sheet (things you should be able to explain)

- **Why a hybrid score?** Skills are exact and explainable; semantic similarity catches related wording; experience and education add context. Weights are configurable.
- **Why TF-IDF by default?** Fast, deterministic, no heavy model download. Embeddings are optional.
- **How is bias reduced?** Scoring only sees skills, experience, education level and de-identified text.
- **Why keep `raw_text` and parsed JSON?** Re-scoring without re-parsing when weights change.
- **How is an upload kept safe?** Size cap, magic bytes, extension allow-list, UUID filename, private storage, authenticated download.
- **How does auth work?** Argon2/bcrypt hashing, short-lived access JWT plus refresh token, role dependency, owner-scoped queries.
- **Why is there no auto-reject?** Screening is decision support; a human decides.

---

## 19. Working Tips for Antigravity

- One phase per conversation. Big "build everything" prompts produce shallow, inconsistent code.
- Make the agent plan first. Fix mistakes in the plan before it writes code.
- Run the code yourself after each phase. Agents can claim success when something is broken.
- Commit after each phase so you can roll back.
- Ask for explanations of the parser, scorer and auth flow. You will be asked about them in your viva.
- Use synthetic resumes (or ones with explicit permission) for demos.
- If the agent wants to add a dependency, change the formula or add a table, it must ask first.

---

## 20. Later (after college submission do not do this without my approval)

Automated tests (pytest, Vitest), ranking-accuracy evaluation (precision@k), Dockerfiles, GitHub Actions CI, cloud deployment, OCR for scanned PDFs, per-job candidate status, LLM-assisted extraction, queue-based batch processing.
