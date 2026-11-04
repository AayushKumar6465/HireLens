# HireLens — Demo Guide

> **Status**: Manual end-to-end browser verification is **PENDING**.
> This guide documents the application features as designed. The user must
> personally complete Steps 6 (browser checklist) to confirm all flows work
> end-to-end in a live environment.

---

## 1. Project Introduction

**HireLens** is an AI-powered, explainable resume screening and candidate ranking system for recruiters.

### Core AI Pipeline

```
Resume Upload (PDF/DOCX)
    └── Validation (size, type, magic bytes, ZIP-bomb, page count)
    └── Async Parsing (pdfplumber → PyMuPDF fallback; python-docx)
        └── NLP Extraction (skills, experience dates, education level, contact)
    └── Hybrid Scoring Engine (pure Python, no PII)
        ├── Skills Match      (keyword + alias matching, required 2x weight)
        ├── Semantic Similarity (TF-IDF cosine, monotonically rescaled)
        ├── Experience Score  (years ratio with merged overlapping intervals)
        └── Education Score   (standardised degree hierarchy rank)
    └── Ranked Results with Full Explainability (matched skills, missing skills, evidence snippets, notes)
```

### Supporting Recruiter Tools
- **Dashboard** — Live analytics: score distribution chart, pipeline funnel, recent screenings
- **Job Management** — Create jobs with AI requirement extraction, skill tagging, education/experience criteria
- **Candidate Pipeline** — Stage management (New → Screening → Interview → Offer → Rejected)
- **Score Drawer** — Per-candidate explainability: sub-scores, weight bars, evidence snippets, missing skills
- **Comparison View** — Side-by-side comparison of 2–4 candidates with unified skill matrix
- **Settings** — Scoring weight customisation (40/30/20/10 defaults) with re-score-all capability
- **CSV Export** — Full ranked list exportable per job
- **Dark Mode** — Persisted theme preference

---

## 2. Local Startup Commands (Windows PowerShell)

### Backend (FastAPI)
```powershell
cd C:\Users\aayus\Desktop\Projects\HireLens\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
Backend available at: `http://localhost:8000`
API docs (Swagger): `http://localhost:8000/docs`

### Frontend (Vite + React)
```powershell
cd C:\Users\aayus\Desktop\Projects\HireLens\frontend
npm run dev
```
Frontend available at: `http://localhost:5173`

> Both must run simultaneously. Start the backend first.

---

## 3. Login / Register Procedure

1. Open `http://localhost:5173` in a browser.
2. Click **Create recruiter account** (or navigate to `/register`).
3. Fill in:
   - **Full Name**: Any name (e.g. `Demo Recruiter`)
   - **Work Email**: Any valid-format email you choose (no real email required; this is local)
   - **Password**: Minimum 8 characters
4. After registration, the app auto-redirects to the Jobs list.
5. For subsequent logins, use the same email and password at `/login`.

> **No passwords or emails are listed in this document.**
> The application stores credentials using Argon2id hashing.

---

## 4. Recruiter Workflow

```
Register → Create Job Opening → Upload Resumes → Run Match → Review Rankings
       → Open Candidate Drawer → Change Pipeline Stage → Compare Candidates
       → Export CSV → Adjust Weights → Re-score All
```

---

## 5. AI Scoring Explanation

### Default Formula (source: `docs/scoring.md`, `backend/app/services/matching/ranker.py`)

$$\text{Total Score} = w_{\text{skills}} \cdot S_{\text{skills}} + w_{\text{semantic}} \cdot S_{\text{semantic}} + w_{\text{exp}} \cdot S_{\text{exp}} + w_{\text{edu}} \cdot S_{\text{edu}}$$

Default weights: **Skills 40% / Semantic 30% / Experience 20% / Education 10%**

### Sub-Score Definitions

| Component | Weight | Method |
|-----------|--------|--------|
| Skills Match | 40% | Keyword + alias matching against taxonomy. Required skills carry **2× weight**. |
| Semantic Similarity | 30% | TF-IDF cosine (unigram + bigram, sublinear TF). Raw cosine `[0.05, 0.50]` mapped to `[0, 100]`. |
| Experience Score | 20% | `min(100, candidate_years / required_years × 100)`. Caps at 100 if candidate meets requirement. |
| Education Score | 10% | Hierarchy rank: doctorate(5) > master(4) > bachelor(3) > associate(2) > high_school(1). |

### Worked Example (from `docs/scoring.md`)

**Job**: Python (req), PostgreSQL (req), Docker (pref). Min exp: 4 yrs. Education: bachelor.

**Candidate A**: Python ✓, PostgreSQL ✓, Docker ✗. Experience: 3 yrs. Education: B.Tech.

| Component | Calculation | Score |
|-----------|-------------|-------|
| Skills | Matched weight 4.0 / Total 5.0 × 100 | **80.0** |
| Semantic | cosine 0.32 → (0.32−0.05)/(0.50−0.05) × 100 | **60.0** |
| Experience | (3.0 / 4.0) × 100 | **75.0** |
| Education | B.Tech = rank 3, Required = rank 3 → meets requirement | **100.0** |
| **Total** | 0.40×80 + 0.30×60 + 0.20×75 + 0.10×100 | **75.0** |

### Weight Renormalization (Missing Components)

If a job has **no minimum experience** set, the experience component is excluded (`null` score, `null` weight). The remaining three weights are renormalized proportionally so they still sum to 1.0:

- Default: Skills 40%, Semantic 30%, Edu 10% → sum = 80%
- Renormalized: Skills 50%, Semantic 37.5%, Edu 12.5%

This is documented in the Score Drawer's "Algorithm Explanation Notes" section.

---

## 6. Synthetic Demo Data

Six resume files are in `demo_assets/resumes/` (git-ignored, not committed):

| # | File | Profile | Expected Outcome |
|---|------|---------|-----------------|
| 1 | `strong_fullstack.pdf` | Arjun Mehta — 5 yrs, Python/FastAPI/SQL/Docker/React, B.Tech | **Strong** match |
| 2 | `medium_backend.docx` | Priya Sharma — 3 yrs, Python/SQL/Django, no Docker, Bachelor | **Medium** match |
| 3 | `partial_junior.pdf` | Rahul Verma — 1 yr intern, Python only, pursuing degree | **Weak** match |
| 4 | `weak_unrelated.docx` | Kavitha Rajan — Marketing manager, no tech skills, MBA | **Near-zero** match |
| 5 | `data_analyst.pdf` | Sanjana Iyer — 2 yrs, SQL + Python (data), no Docker, B.Sc. | **Moderate** match |
| 6 | `scanned_image_only.pdf` | Image-only PDF — zero text layer | **Parse FAILED** (`scanned_or_empty`) |

All identities are completely fictional. Emails use `@example.com`. Phone numbers use 555-style.
Exact scores are computed by the engine at upload time and are not predicted here.

---

## 7. 15-Step Demo Sequence

> **REQUIRES MANUAL BROWSER VERIFICATION** for each step.

1. **Login** — Navigate to `/login`. Enter your registered credentials. Confirm redirect to Jobs list.
2. **Dashboard** — Click Dashboard. Confirm score distribution chart and pipeline funnel render (or show empty-state messages if no data yet).
3. **Settings — Reset Weights** — Go to Settings. Click "Reset to Standard Defaults (40 / 30 / 20 / 10)". Confirm all four sliders return to defaults. Observe "Total: 100% ✓ Valid" badge.
4. **Create Job Opening** — Click "New Job Opening". Fill:
   - Title: `Python Backend Engineer`
   - Min Experience: `3`
   - Education: `Bachelor's Degree`
   - Add skills: `Python` (required), `SQL` (required), `Docker` (required), `FastAPI` (preferred), `React` (preferred)
   - Description: paste a few lines about the role
   - Submit → confirm redirect to Job Detail page.
5. **Upload Tab** — Click "Resume Upload Hub" tab. Confirm dropzone renders with "PDF and DOCX, batch limit 20, max 5 MB per file" text.
6. **Upload 5 Parseable Resumes** — Drag-and-drop files 1–5. Confirm upload feedback shows all 5 as uploaded. Observe spinning loader with "Processing & scoring in background..." message.
7. **Upload Scanned PDF** — Upload `scanned_image_only.pdf` separately. After polling, confirm "Parsing Failures" section appears listing the resume with reason `scanned_or_empty` or similar.
8. **Run Match** — Click "Run Match" button (or wait for auto-score polling to complete). Confirm Candidate Rankings tab populates with scored entries.
9. **Ranking Order Sanity** — Confirm order is approximately: Arjun > Priya > Sanjana > Rahul > Kavitha. (Exact order depends on engine output.)
10. **Score Drawer** — Click "Details" for the top candidate. Confirm:
    - Score bars with correct weights (40%/30%/20%/10%)
    - Matched skills with text evidence snippets
    - Missing required skills section
    - Algorithm Explanation Notes
11. **Status Change** — In the drawer or table dropdown, change a candidate's stage from "New" to "Screening". Confirm the stage badge updates immediately.
12. **Compare Candidates** — Select 2–4 candidates using checkboxes. Click "Compare". Confirm the comparison modal opens with candidate summary cards and the unified skill matrix showing ✓/✗ per candidate per skill.
13. **Bulk Shortlist** — Select 2 candidates. Click "Shortlist". Confirm both update to "Screening" stage. Then select 1 candidate and click "Reject". Confirm the rejection confirmation dialog appears (never auto-rejects).
14. **Dark Mode** — Click the theme toggle button (moon/sun icon). Confirm the entire UI switches theme. Toggle back. Confirm persistence on page reload.
15. **Export CSV** — Click "Export CSV" on the Job Detail page. Confirm a `.csv` file downloads with columns: Rank, Candidate Name, Email, Status, Total Score, Skill Score, Semantic Score, Experience Score, Education Score, Matched Skills, Missing Required Skills.

---

## 8. Known Limitations

- **No automated tests**: No unit or integration test suite was written during development. Core flow was verified end-to-end manually.
- **TF-IDF, not deep semantic**: Semantic similarity uses TF-IDF cosine, not transformer embeddings. It measures lexical overlap, not true semantic understanding.
- **Rule-based parsing**: Experience and education are extracted by regex and keyword matching. Unusual resume formats may parse incorrectly.
- **Scanned PDFs unsupported**: Image-only PDFs (no text layer) cannot be processed. No OCR capability is included.
- **No real-time updates**: Polling is capped at 25 attempts (≈37.5 seconds). Very slow parse operations may show as still-pending after the polling window.
- **Single-file per candidate**: Each uploaded resume creates one candidate record. There is no mechanism to merge multiple resumes for the same person.
- **Local storage only**: Resume files are stored on the local filesystem under `backend/storage/resumes/`. No cloud storage integration.
- **No email notifications**: The system does not send emails to candidates or recruiters.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Backend not starting | Missing `.env` or DB unreachable | Check `backend/.env` exists and `DATABASE_URL` points to Neon correctly |
| CORS error in browser | Frontend URL not in CORS allow-list | Confirm `FRONTEND_URL` in `.env` matches the running frontend URL (default `http://localhost:5173`) |
| Polling timeout / "Processing..." forever | Resume parse worker hung | Refresh the page; use "Run Match" button manually; check backend logs |
| Scanned PDF "failed" | Expected — image-only PDF has no text layer | No fix needed; this demonstrates the `scanned_or_empty` error state |
| Weights show wrong values | DB `app_settings` has stale entry | Go to Settings → Reset to Defaults → Save Weights & Re-score |
| Upload rejected with "5 MB limit" | File too large | Use files under 5 MB; each demo file in `demo_assets/resumes/` is well within limit |
| `npm run dev` port conflict | Port 5173 in use | Run `npx vite --port 5174` or kill the conflicting process |
