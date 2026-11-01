import os
from functools import lru_cache
import re

# Ensure local offline operation so HF Hub does not perform remote checks
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model_failed = False


@lru_cache(maxsize=1)
def load_model():
    """Load the pretrained sentence transformer model once, caching it."""
    global _model_failed
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(MODEL_NAME)
    except Exception:
        _model_failed = True
        return None


def collect_text(value, preferred_keys=None):
    """Collect readable text from nested parser/analyzer results."""
    preferred_keys = preferred_keys or {
        "text",
        "raw_text",
        "extracted_text",
        "resume_text",
        "content",
        "education_text",
        "experience_text",
        "projects_text",
        "skills_found",
        "skills",
        "profile",
    }

    parts = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in preferred_keys:
                text = collect_text(item, preferred_keys)
                if text:
                    parts.append(text)

        if not parts:
            for key, item in value.items():
                if isinstance(item, (dict, list, tuple, str)):
                    text = collect_text(item, preferred_keys)
                    if text:
                        parts.append(text)

    elif isinstance(value, (list, tuple)):
        for item in value:
            text = collect_text(item, preferred_keys)
            if text:
                parts.append(text)

    elif isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            parts.append(cleaned)

    return "\n".join(parts)


def tfidf_similarity(resume_text: str, job_text: str) -> float:
    """Fast, local TF-IDF cosine similarity fallback."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    matrix = vectorizer.fit_transform([resume_text, job_text])
    sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return round(max(0.0, min(1.0, float(sim))) * 100, 2)


def calculate_semantic_similarity(resume_data, job_description):
    """
    Estimate semantic similarity between extracted resume content
    and the job description. Tries SentenceTransformers with seamless
    fallback to scikit-learn TF-IDF. This is not a hiring probability.
    """
    resume_text = collect_text(resume_data)
    job_text = (job_description or "").strip()

    if not resume_text:
        return {
            "available": False,
            "model": MODEL_NAME,
            "similarity_percent": None,
            "explanation": "No readable resume text was available for semantic analysis.",
        }

    if not job_text:
        return {
            "available": False,
            "model": MODEL_NAME,
            "similarity_percent": None,
            "explanation": "The job description is empty.",
        }

    # Try transformer model first
    try:
        model = load_model()
        if model is not None:
            from sentence_transformers import util
            embeddings = model.encode(
                [resume_text, job_text],
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
            similarity_percent = round(max(0.0, min(1.0, similarity)) * 100, 2)
            return {
                "available": True,
                "model": MODEL_NAME,
                "engine": "sentence_transformers",
                "similarity_percent": similarity_percent,
                "score_type": "dense_embedding_cosine_similarity",
                "explanation": (
                    "Dense semantic embedding similarity between extracted resume "
                    "text and the job description. Represents evidence alignment, not job success."
                ),
            }
    except Exception:
        pass

    # Seamless fallback to local TF-IDF cosine similarity
    try:
        score = tfidf_similarity(resume_text, job_text)
        return {
            "available": True,
            "model": "scikit-learn TF-IDF",
            "engine": "tfidf_cosine_similarity",
            "similarity_percent": score,
            "score_type": "tfidf_cosine_similarity",
            "explanation": (
                "TF-IDF textual relevance similarity between resume and job description. "
                "Represents vocabulary relevance, not candidate ability."
            ),
        }
    except Exception as err:
        return {
            "available": False,
            "model": "none",
            "similarity_percent": None,
            "explanation": f"Semantic analysis could not be calculated: {err}",
        }
