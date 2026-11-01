import json
import pytest
from resume_analyzer import (
    analyze_resume,
    detect_sections,
    estimate_experience_years,
    extract_profile,
    extract_skill_evidence,
    find_skills,
)


def test_detect_sections():
    text = (
        "John Doe\nDeveloper\n\n"
        "Skills:\nPython, React, Docker\n\n"
        "Experience:\n3 years at Corp\n\n"
        "Education:\nBS Computer Science"
    )
    sections = detect_sections(text)
    assert "skills" in sections
    assert "experience" in sections
    assert "education" in sections


def test_find_skills():
    text = "Proficient in Python, React.js, PostgreSQL, and Git version control."
    skills = find_skills(text)
    assert "python" in skills
    assert "react" in skills
    assert "postgresql" in skills
    assert "git" in skills


def test_extract_profile():
    text = "Jane Smith\nData Scientist\njane.smith@example.com | (555) 123-4567\n"
    sections = {"other": "Jane Smith\nData Scientist"}
    profile = extract_profile(text, sections)
    assert profile["full_name"] == "Jane Smith"
    assert profile["email"] == "jane.smith@example.com"
    assert "555" in profile["phone"]


def test_estimate_experience_years():
    assert estimate_experience_years("3 years of experience in Python") == 3.0
    assert estimate_experience_years("Senior Dev with 5+ yrs experience") == 5.0
    assert estimate_experience_years("No date mentioned here") is None


def test_extract_skill_evidence():
    text = "Built web applications using Python and FastAPI.\nConfigured Docker containers."
    evidence = extract_skill_evidence(text, ["python", "docker"])
    assert "python" in evidence
    assert any("Python and FastAPI" in s for s in evidence["python"])


def test_analyze_resume_full(tmp_path):
    parsed_json_path = tmp_path / "parsed.json"
    parsed_json_path.write_text(
        json.dumps({
            "file_name": "resume.txt",
            "text": "David Miller\nEngineer\ndavid@test.com\n\nSkills:\nPython, SQL, React\n\nExperience:\n2 years experience in web development."
        }),
        encoding="utf-8",
    )
    res = analyze_resume(parsed_json_path)
    assert res["profile"]["full_name"] == "David Miller"
    assert "python" in res["skills_found"]
    assert "sql" in res["skills_found"]
    assert res["experience_years_detected"] == 2.0
