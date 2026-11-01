import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_dashboard_stats():
    res = client.get("/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_jobs" in data
    assert "total_applications" in data
    assert "shortlisted_candidates" in data


def test_jobs_crud():
    # 1. Create Job
    job_payload = {
        "title": "Backend Python Developer",
        "department": "Engineering",
        "description": "Develop scalable APIs with FastAPI.\n\nRequired Skills:\nPython, SQL, Git\n\nPreferred Skills:\nDocker, AWS",
        "required_skills": ["python", "sql", "git"],
        "preferred_skills": ["docker", "aws"],
        "min_experience_years": 2.0,
        "location": "Remote",
    }
    create_res = client.post("/jobs", json=job_payload)
    assert create_res.status_code == 200
    job = create_res.json()["job"]
    job_id = job["id"]
    assert job["title"] == "Backend Python Developer"

    # 2. Get Job Detail
    get_res = client.get(f"/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["job"]["id"] == job_id

    # 3. Update Job
    patch_res = client.patch(f"/jobs/{job_id}", json={"status": "paused", "department": "Core Platform"})
    assert patch_res.status_code == 200
    assert patch_res.json()["job"]["status"] == "paused"
    assert patch_res.json()["job"]["department"] == "Core Platform"

    # 4. List Jobs
    list_res = client.get("/jobs")
    assert list_res.status_code == 200
    assert any(j["id"] == job_id for j in list_res.json()["jobs"])


def test_screen_resumes_batch():
    # 1. Create a test job
    job_res = client.post(
        "/jobs",
        json={
            "title": "QA Test Engineer",
            "department": "QA",
            "description": "Looking for test engineer.\nRequired Skills:\nPython, Git\nPreferred Skills:\nDocker",
            "required_skills": ["python", "git"],
            "preferred_skills": ["docker"],
        },
    )
    job_id = job_res.json()["job"]["id"]

    # 2. Upload synthetic resume txt file
    resume_content = b"Candidate Test\nQA Engineer\ntest@example.com\n\nSkills:\nPython, Git, Docker\n\nExperience:\n1 year testing."
    files = [
        ("files", ("cand_test.txt", io.BytesIO(resume_content), "text/plain")),
    ]

    screen_res = client.post(f"/jobs/{job_id}/screen", files=files)
    assert screen_res.status_code == 200
    data = screen_res.json()
    assert data["status"] == "completed"
    assert data["processed_count"] == 1
    assert data["results"][0]["overall_score"] == 100.0  # 2 req + 1 pref matched!
    app_id = data["results"][0]["application_id"]

    # 3. Retrieve application detail
    app_res = client.get(f"/applications/{app_id}")
    assert app_res.status_code == 200
    app_detail = app_res.json()["application"]
    assert app_detail["candidate_name"] == "Candidate Test"
    assert app_detail["hr_status"] == "applied"

    # 4. Update HR status to shortlisted
    status_res = client.patch(
        f"/applications/{app_id}/status",
        json={"status": "shortlisted", "note": "Perfect test match."},
    )
    assert status_res.status_code == 200
    assert status_res.json()["application"]["hr_status"] == "shortlisted"

    # 5. Check status history
    hist_res = client.get(f"/applications/{app_id}/history")
    assert hist_res.status_code == 200
    history = hist_res.json()["status_history"]
    assert any(h["new_status"] == "shortlisted" for h in history)

    # 6. Update notes
    note_res = client.patch(
        f"/applications/{app_id}/notes",
        json={"notes": "Interview scheduled for next Tuesday."},
    )
    assert note_res.status_code == 200
    assert note_res.json()["application"]["notes"] == "Interview scheduled for next Tuesday."

    # 7. Export CSV
    csv_res = client.get(f"/jobs/{job_id}/export.csv")
    assert csv_res.status_code == 200
    assert "Candidate Test" in csv_res.text
    assert "text/csv" in csv_res.headers.get("content-type", "")


def test_fairness_audit_endpoint():
    res = client.get("/fairness/audit")
    assert res.status_code == 200
    data = res.json()
    assert data["absolute_score_gap"] == 0.0
    assert "PASS" in data["status"]
    assert len(data["excluded_features"]) >= 5
