"""
Semantic similarity matching between job descriptions and resume text.

Implements TF-IDF vectorization with cosine similarity and monotonic 0-100 rescaling.
Pure Python/scikit-learn implementation: no database or HTTP dependencies.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Calibration thresholds for mapping raw TF-IDF cosine to a calibrated 0-100 score
MIN_COSINE_THRESHOLD = 0.05
MAX_COSINE_THRESHOLD = 0.50


def rescale_cosine_similarity(raw_cosine: float) -> float:
    """
    Monotonically rescale raw TF-IDF cosine similarity to a 0-100 score.

    Raw cosine for resumes typically spans [0.05, 0.50].
    Values <= 0.05 map to 0.0, and values >= 0.50 map to 100.0.
    """
    if raw_cosine <= MIN_COSINE_THRESHOLD:
        return 0.0
    if raw_cosine >= MAX_COSINE_THRESHOLD:
        return 100.0

    scaled = (
        (raw_cosine - MIN_COSINE_THRESHOLD)
        / (MAX_COSINE_THRESHOLD - MIN_COSINE_THRESHOLD)
    ) * 100.0
    return round(min(100.0, max(0.0, scaled)), 1)


def calculate_semantic_similarity(
    job_description: str,
    resume_text: str,
) -> float | None:
    """
    Calculate normalized semantic similarity score between job description and resume text.

    Returns a float in [0.0, 100.0], or None if either input is empty.
    """
    clean_job = job_description.strip()
    clean_resume = resume_text.strip()

    if not clean_job or not clean_resume:
        return None

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform([clean_job, clean_resume])
        sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        raw_cosine = float(sim_matrix[0][0])
        return rescale_cosine_similarity(raw_cosine)
    except (ValueError, TypeError, AttributeError, RuntimeError):
        return 0.0
