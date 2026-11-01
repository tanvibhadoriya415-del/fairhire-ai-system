import pytest
from job_matcher import calculate_match, extract_job_skills, normalize_skill


def test_normalize_skill():
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("  PYTHON  ") == "python"
    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("REST APIs") == "rest api"


def test_extract_job_skills():
    job_text = (
        "Job Title: Software Engineer\n\n"
        "Required Skills:\nPython, SQL, React, Git\n\n"
        "Preferred Skills:\nMachine Learning, Docker\n"
    )
    req, pref = extract_job_skills(job_text)
    assert "python" in req
    assert "sql" in req
    assert "react" in req
    assert "git" in req
    assert "machine learning" in pref
    assert "docker" in pref


def test_calculate_match_aarav_baseline():
    """
    Tests the Aarav Sharma test case:
    Resume has: Python, SQL, Git, React, Machine Learning
    Job requires: Python, SQL, Git, React (4 skills * weight 2 = 8 points)
    Job prefers: Machine Learning, REST API, Docker (3 skills * weight 1 = 3 points)
    Total possible = 8 + 3 = 11 points
    Earned = 8 (all 4 required) + 1 (Machine Learning) = 9 points
    Score = 9 / 11 = 81.82%
    """
    resume_skills = ["git", "machine learning", "python", "react", "sql"]
    required_skills = ["python", "sql", "git", "react"]
    preferred_skills = ["machine learning", "rest api", "docker"]

    result = calculate_match(resume_skills, required_skills, preferred_skills)
    assert result["score_percent"] == 81.82
    assert result["required_skill_coverage"] == 100.0
    assert len(result["matched_required_skills"]) == 4
    assert result["missing_required_skills"] == []
    assert result["matched_preferred_skills"] == ["machine learning"]
    assert sorted(result["missing_preferred_skills"]) == ["docker", "rest api"]


def test_candidate_different_scores_for_different_jobs():
    """Confirms candidate gets different scores for two different job descriptions."""
    candidate_skills = ["python", "pandas", "numpy", "sql", "data analysis"]

    # Job A: Data Analyst
    job_a_req = ["python", "sql", "data analysis", "pandas"]
    job_a_pref = ["tableau", "machine learning"]
    res_a = calculate_match(candidate_skills, job_a_req, job_a_pref)

    # Job B: Frontend Developer
    job_b_req = ["react", "typescript", "html", "css", "git"]
    job_b_pref = ["figma", "node.js"]
    res_b = calculate_match(candidate_skills, job_b_req, job_b_pref)

    # Candidate matches 100% of required for Data Analyst, 0% for Frontend
    assert res_a["required_skill_coverage"] == 100.0
    assert res_a["score_percent"] > 70.0

    assert res_b["required_skill_coverage"] == 0.0
    assert res_b["score_percent"] == 0.0


def test_zero_required_skills_handling():
    result = calculate_match(["python"], [], ["python"])
    assert result["score_percent"] == 100.0
    assert result["required_skill_coverage"] == 100.0
