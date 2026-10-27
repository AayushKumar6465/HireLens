# HireLens Scoring and Explainability Specification

## 1. Overview and Hybrid Formula

HireLens evaluates candidate resumes against job opening requirements using an explainable, transparent hybrid scoring model. Every candidate match yields an overall `total_score` (normalized to $[0.0, 100.0]$) alongside a complete `ScoreBreakdown` object containing itemized sub-scores, evidence snippets, matched/missing skills, and calculation notes.

A candidate score is **decision support** for human recruiters; HireLens **never** automatically rejects any candidate.

### Default Scoring Formula
$$\text{Total Score} = 0.40 \cdot S_{\text{skills}} + 0.30 \cdot S_{\text{semantic}} + 0.20 \cdot S_{\text{exp}} + 0.10 \cdot S_{\text{edu}}$$

Weights may be overridden per job posting (`weights_override`), but must always sum to $1.0$.

---

## 2. Sub-Score Definitions

### 2.1 Skill Score ($S_{\text{skills}}$)
* **Rule**:
  * Job skill requirements designated as `required` carry **$2\times$ the weight** of `preferred` skills.
  * Formula:
    $$S_{\text{skills}} = \min\left(100.0, \max\left(0.0, \frac{\text{Matched Weight}}{\text{Total Requirement Weight}} \times 100.0\right)\right)$$
* **Evidence**: For every matched skill, HireLens records the canonical name, match type (`exact` or `alias`), the section where it was found, and a short surrounding text snippet ($\le 120$ characters).
* **Missing Skills**: Unmatched requirements are categorized into `missing_required` and `missing_preferred`. Extra candidate skills not requested by the job are listed in `extra_skills`.

### 2.2 Semantic Score ($S_{\text{semantic}}$)
* **Method**: TF-IDF unigram and bigram vectorization with sublinear term-frequency scaling and cosine similarity.
* **Monotonic Rescaling**: Raw TF-IDF cosine similarity between resume text and job postings typically falls within $[0.05, 0.50]$. Raw cosine is mapped monotonically to $[0.0, 100.0]$:
  $$\text{Calibrated Score} = \begin{cases} 
  0.0 & \text{if } \text{cosine} \le 0.05 \\
  100.0 & \text{if } \text{cosine} \ge 0.50 \\
  \frac{\text{cosine} - 0.05}{0.50 - 0.05} \times 100.0 & \text{otherwise}
  \end{cases}$$
* Strips all PII (names, contact info, emails, phones, URLs) before vectorization.

### 2.3 Experience Score ($S_{\text{exp}}$)
* **Rule**:
  * If Candidate Experience $\ge$ Job Minimum Experience: $S_{\text{exp}} = 100.0$.
  * If Candidate Experience $<$ Job Minimum Experience:
    $$S_{\text{exp}} = \min\left(100.0, \max\left(0.0, \frac{\text{Candidate Years}}{\text{Required Years}} \times 100.0\right)\right)$$
* **Overlapping Period Merging**: Employment periods are converted into month intervals and merged. Concurrent jobs or concurrent freelancing do not artificially inflate total years.

### 2.4 Education Score ($S_{\text{edu}}$)
* **Hierarchy**:
  1. `doctorate` (Rank 5)
  2. `master` (Rank 4)
  3. `bachelor` (Rank 3)
  4. `associate` (Rank 2)
  5. `high_school` (Rank 1)
* **Rule**:
  * If Candidate Rank $\ge$ Required Rank: $S_{\text{edu}} = 100.0$.
  * If Candidate Rank $<$ Required Rank:
    $$S_{\text{edu}} = \min\left(100.0, \max\left(0.0, \frac{\text{Candidate Rank}}{\text{Required Rank}} \times 100.0\right)\right)$$

---

## 3. Missing Component Handling & Weight Renormalization

If a job posting omits a requirement (e.g. no skills specified, no minimum experience, or no degree requirement):
1. That component is **not** assigned a fake $0$ or $100$ score.
2. The omitted component is marked `null` in `sub_scores` and `null` in `weights_used`.
3. The remaining active weights are **renormalized proportionally** so that their sum equals $1.0$:
   $$w_i' = \frac{w_i}{\sum_{j \in \text{Active}} w_j}$$
4. An explanatory note is appended to `notes` (e.g. *"No minimum experience requirement defined; experience score was excluded."*).

---

## 4. Bias Mitigation and Privacy

* **Exclusion of Protected Attributes**: Candidate name, gender, age, photo, address, nationality, and contact details **never** enter the scoring functions.
* **Pure Functions**: All scoring modules in `app/services/matching/` are pure Python functions without database or network dependencies.
* **No Auto-Rejection**: Recruiters make all hiring decisions. Scores serve as ranking suggestions.

---

## 5. Worked Hand-Checked Example

**Job Opening**:
* Title: Senior Backend Engineer
* Description: Building scalable APIs with Python, PostgreSQL, and Docker.
* Requirements:
  * Python (Required, weight: 1.0 $\implies$ effective weight: 2.0)
  * PostgreSQL (Required, weight: 1.0 $\implies$ effective weight: 2.0)
  * Docker (Preferred, weight: 1.0 $\implies$ effective weight: 1.0)
  * Total Requirement Weight = $2.0 + 2.0 + 1.0 = 5.0$
* Min Experience: 4.0 years
* Education Level: `bachelor` (Rank 3)

**Candidate A**:
* Skills: Python (exact match, snippet: "REST APIs in Python"), PostgreSQL (alias match, snippet: "managed PostgreSQL db"). Missing Docker.
* Matched Weight: $2.0 + 2.0 = 4.0$
* $S_{\text{skills}} = (4.0 / 5.0) \times 100.0 = \mathbf{80.0}$
* Raw TF-IDF Cosine: $0.32$
  * $S_{\text{semantic}} = ((0.32 - 0.05) / (0.50 - 0.05)) \times 100.0 = (0.27 / 0.45) \times 100.0 = \mathbf{60.0}$
* Total Experience: 3.0 years (vs 4.0 required)
  * $S_{\text{exp}} = (3.0 / 4.0) \times 100.0 = \mathbf{75.0}$
* Education: B.Tech Computer Science $\implies$ `bachelor` (Rank 3 vs Rank 3)
  * $S_{\text{edu}} = \mathbf{100.0}$

**Calculated Total Score**:
$$\text{Total} = 0.40 \times 80.0 + 0.30 \times 60.0 + 0.20 \times 75.0 + 0.10 \times 100.0$$
$$\text{Total} = 32.0 + 18.0 + 15.0 + 10.0 = \mathbf{75.0}$$

This exact hand calculation matches the engine's programmatic output.
