import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from backend.database import (
    create_job,
    create_or_get_application,
    get_application_detail,
    get_dashboard_stats,
    get_job,
    list_applications_for_job,
    list_audit_events,
    list_jobs,
    record_audit_event,
    save_or_update_candidate,
    save_screening_result,
    update_application_notes,
    update_application_status,
    update_job,
    STORAGE_DIR,
)
from backend.fairness_audit import run_fairness_audit
from backend.semantic_matcher import calculate_semantic_similarity
from job_matcher import calculate_match, extract_job_skills, normalize_skill
from resume_analyzer import analyze_resume
from resume_parser import parse_resume

app = FastAPI(
    title="FairHire AI - Explainable and Bias-Aware Resume Screening System",
    description=(
        "Production-ready HR recruitment screening platform featuring "
        "job-specific candidate evaluation, transparent weighted matching, "
        "dense/TF-IDF semantic relevance, bias guardrails, and persistent audit trails."
    ),
    version="1.0.0",
)

# CORS configuration for local React / Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ============================================================================
# Request Models
# ============================================================================

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=5)
    department: str = Field("Engineering", max_length=100)
    responsibilities: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    education_requirement: str = ""
    employment_type: str = "Full-time"
    location: str = "Remote / Hybrid"
    status: str = "active"


class JobUpdateRequest(BaseModel):
    title: str | None = None
    department: str | None = None
    description: str | None = None
    responsibilities: str | None = None
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    min_experience_years: float | None = None
    education_requirement: str | None = None
    employment_type: str | None = None
    location: str | None = None
    status: str | None = None


class JobParseSkillsRequest(BaseModel):
    description: str


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="applied, under_review, shortlisted, interview_scheduled, offer_pending, rejected")
    note: str = ""


class NoteUpdateRequest(BaseModel):
    notes: str


# ============================================================================
# Helpers
# ============================================================================

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)
    return cleaned or "resume.pdf"


def process_single_resume(
    contents: bytes,
    filename: str,
    job: dict,
):
    """Processes a single resume against a job and returns structured results."""
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{extension}'. Only PDF, DOCX, and TXT are accepted.")

    if not contents or len(contents) == 0:
        raise ValueError("The uploaded file is empty.")

    if len(contents) > MAX_FILE_SIZE:
        raise ValueError("File exceeds maximum allowed size of 10 MB.")

    resume_hash = hashlib.sha256(contents).hexdigest()
    safe_name = sanitize_filename(filename)
    stored_path = STORAGE_DIR / f"{resume_hash[:16]}_{safe_name}"

    # Retain original document securely
    try:
        stored_path.write_bytes(contents)
    except Exception as err:
        raise RuntimeError(f"Could not persist resume file: {err}") from err

    # Parse in temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_workspace = Path(temp_dir)
        temp_resume = temp_workspace / f"resume{extension}"
        temp_parsed = temp_workspace / "parsed.json"

        temp_resume.write_bytes(contents)
        parsed = parse_resume(temp_resume)
        temp_parsed.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
        structured = analyze_resume(temp_parsed)

    # Candidate profile fields
    profile = structured.get("profile", {})
    cand_name = profile.get("full_name") or safe_name.replace(extension, "").replace("_", " ").title()
    cand_email = profile.get("email")
    cand_phone = profile.get("phone")
    cand_headline = profile.get("headline")
    cand_summary = profile.get("summary")
    skills_found = structured.get("skills_found", [])
    evidence_map = structured.get("skill_evidence", {})
    exp_years = structured.get("experience_years_detected")
    raw_text = parsed.get("text", "")

    # Job requirements
    req_skills = job.get("required_skills", [])
    pref_skills = job.get("preferred_skills", [])

    # If job has no explicit required/preferred skills in DB, extract on the fly from description
    if not req_skills and not pref_skills:
        extracted_req, extracted_pref = extract_job_skills(job.get("description", ""))
        req_skills = extracted_req
        pref_skills = extracted_pref

    # Transparent Match Calculation
    matching = calculate_match(
        resume_skills=skills_found,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        skill_evidence=evidence_map,
    )

    # Semantic relevance
    semantic = calculate_semantic_similarity(
        {"text": raw_text, "structured": structured},
        job.get("description", ""),
    )

    skill_score = matching["score_percent"]
    coverage = matching["required_skill_coverage"]
    overall_score = skill_score  # Transparent primary score

    # Save to Database
    candidate_id = save_or_update_candidate(
        name=cand_name,
        resume_hash=resume_hash,
        raw_text=raw_text,
        skills=skills_found,
        email=cand_email,
        phone=cand_phone,
        headline=cand_headline,
        summary=cand_summary,
        education_text=structured.get("education_text", ""),
        experience_text=structured.get("experience_text", ""),
        experience_years_detected=exp_years,
        projects_text=structured.get("projects_text", ""),
        certifications_text=structured.get("certifications_text", ""),
        filename=safe_name,
    )

    application_id = create_or_get_application(
        candidate_id=candidate_id,
        job_id=job["id"],
        original_filename=safe_name,
        stored_filepath=str(stored_path),
        file_type=extension.lstrip("."),
        processing_status="completed",
    )

    save_screening_result(
        application_id=application_id,
        job_id=job["id"],
        candidate_id=candidate_id,
        overall_score=overall_score,
        skill_score=skill_score,
        required_skill_coverage=coverage,
        semantic_score=semantic.get("similarity_percent"),
        matched_required_skills=matching["matched_required_skills"],
        missing_required_skills=matching["missing_required_skills"],
        matched_preferred_skills=matching["matched_preferred_skills"],
        missing_preferred_skills=matching["missing_preferred_skills"],
        evidence=matching["evidence"],
        score_breakdown=matching["score_breakdown"],
        explanation=matching["explanation"],
        warnings=structured.get("warnings", []),
        scoring_method=matching["scoring_method"],
    )

    return {
        "application_id": application_id,
        "candidate_id": candidate_id,
        "candidate_name": cand_name,
        "filename": safe_name,
        "overall_score": overall_score,
        "skill_score": skill_score,
        "required_skill_coverage": coverage,
        "semantic_score": semantic.get("similarity_percent"),
        "matched_required_skills": matching["matched_required_skills"],
        "missing_required_skills": matching["missing_required_skills"],
        "matched_preferred_skills": matching["matched_preferred_skills"],
        "missing_preferred_skills": matching["missing_preferred_skills"],
        "experience_years_detected": exp_years,
        "warnings": structured.get("warnings", []),
    }


# ============================================================================
# API Routes
# ============================================================================

@app.get("/")
def home():
    return {
        "app": "FairHire AI API",
        "tagline": "Smarter screening. Clearer decisions. Fairer hiring.",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    stats = get_dashboard_stats()
    return {
        "status": "ok",
        "database": "connected",
        "total_jobs": stats["total_jobs"],
        "total_applications": stats["total_applications"],
    }


@app.get("/dashboard/stats")
def dashboard_stats():
    return get_dashboard_stats()


# ----------------------------------------------------------------------------
# Job Endpoints
# ----------------------------------------------------------------------------

@app.get("/jobs")
def get_jobs(search: str | None = None, status: str | None = None):
    jobs = list_jobs(search=search, status=status)
    return {"jobs": jobs, "total": len(jobs)}


@app.post("/jobs")
def add_job(request: JobCreateRequest):
    req_skills = request.required_skills
    pref_skills = request.preferred_skills

    # If no explicit skills were entered, attempt helper extraction from description
    if not req_skills and not pref_skills:
        extracted_req, extracted_pref = extract_job_skills(request.description)
        req_skills = extracted_req
        pref_skills = extracted_pref

    job = create_job(
        title=request.title,
        description=request.description,
        department=request.department,
        responsibilities=request.responsibilities,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        min_experience_years=request.min_experience_years,
        education_requirement=request.education_requirement,
        employment_type=request.employment_type,
        location=request.location,
        status=request.status,
    )
    return {"status": "success", "job": job}


@app.get("/jobs/{job_id}")
def get_job_by_id(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found.")
    return {"job": job}


@app.patch("/jobs/{job_id}")
def patch_job(job_id: int, request: JobUpdateRequest):
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    updated = update_job(job_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Job opening not found.")
    return {"status": "success", "job": updated}


@app.post("/jobs/parse-requirements")
def parse_job_requirements(request: JobParseSkillsRequest):
    """Assists HR by extracting detected skills from job description text for confirmation."""
    text = (request.description or "").strip()
    if not text:
        return {"required_skills": [], "preferred_skills": []}

    req_skills, pref_skills = extract_job_skills(text)
    return {
        "required_skills": req_skills,
        "preferred_skills": pref_skills,
        "suggestion": "Review and confirm extracted skills before publishing the job opening.",
    }


# ----------------------------------------------------------------------------
# Resume Upload & Screening Endpoints
# ----------------------------------------------------------------------------

@app.post("/jobs/{job_id}/resumes")
@app.post("/jobs/{job_id}/screen")
async def screen_resumes_batch(
    job_id: int,
    files: list[UploadFile] = File(...),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found.")

    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one resume.")

    successful = []
    failed = []

    for upload in files:
        filename = sanitize_filename(upload.filename or "resume.pdf")
        try:
            contents = await upload.read()
            res = process_single_resume(contents, filename, job)
            successful.append(res)
        except ValueError as err:
            failed.append({"filename": filename, "error": str(err)})
        except Exception as err:
            failed.append({"filename": filename, "error": f"Screening failure: {err}"})
        finally:
            await upload.close()

    record_audit_event(
        "screening_batch",
        job_id=job_id,
        details={
            "processed": len(successful),
            "failed": len(failed),
            "files": [f["filename"] for f in successful],
        },
    )

    return {
        "status": "completed",
        "job_id": job_id,
        "job_title": job["title"],
        "processed_count": len(successful),
        "failed_count": len(failed),
        "results": successful,
        "errors": failed,
        "notice": (
            "Screening results reflect evidence overlap and semantic relevance against "
            "the current job requirements. All consequential decisions require human review."
        ),
    }


@app.post("/jobs/{job_id}/rescreen")
def rescreen_job_applicants(job_id: int):
    """Re-evaluates all existing applications for a job against updated job requirements."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found.")

    apps = list_applications_for_job(job_id=job_id, limit=500)["candidates"]
    rescreened = 0
    failed = 0

    for app_item in apps:
        app_id = app_item["application_id"]
        detail = get_application_detail(app_id)
        if not detail or not detail.get("stored_filepath"):
            continue

        file_path = Path(detail["stored_filepath"])
        if not file_path.exists():
            failed += 1
            continue

        try:
            contents = file_path.read_bytes()
            process_single_resume(contents, detail["original_filename"], job)
            rescreened += 1
        except Exception:
            failed += 1

    record_audit_event(
        "re_screen",
        job_id=job_id,
        details={"rescreened": rescreened, "failed": failed},
    )

    return {
        "status": "success",
        "job_id": job_id,
        "rescreened_count": rescreened,
        "failed_count": failed,
    }


# ----------------------------------------------------------------------------
# Candidate Explorer & Applications
# ----------------------------------------------------------------------------

@app.get("/jobs/{job_id}/candidates")
def get_job_candidates(
    job_id: int,
    search: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    hr_status: str | None = None,
    processing_status: str | None = None,
    required_skill: str | None = None,
    preferred_skill: str | None = None,
    matched_skill: str | None = None,
    missing_skill: str | None = None,
    min_experience: float | None = None,
    sort_by: str = Query("score_desc", pattern="^(score_desc|score_asc|coverage_desc|coverage_asc|experience_desc|experience_asc|date_desc|date_asc|name_asc|name_desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found.")

    result = list_applications_for_job(
        job_id=job_id,
        search=search,
        min_score=min_score,
        max_score=max_score,
        hr_status=hr_status,
        processing_status=processing_status,
        required_skill=required_skill,
        preferred_skill=preferred_skill,
        matched_skill=matched_skill,
        missing_skill=missing_skill,
        min_experience=min_experience,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    result["job"] = {
        "id": job["id"],
        "title": job["title"],
        "department": job["department"],
        "status": job["status"],
    }
    return result


@app.get("/applications/{application_id}")
def get_candidate_application(application_id: int):
    detail = get_application_detail(application_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Application record not found.")
    return {"application": detail}


@app.patch("/applications/{application_id}/status")
def patch_application_status(application_id: int, request: StatusUpdateRequest):
    try:
        updated = update_application_status(
            application_id=application_id,
            new_status=request.status,
            note=request.note,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Application record not found.")
        return {"status": "success", "application": updated}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err


@app.patch("/applications/{application_id}/notes")
def patch_application_notes(application_id: int, request: NoteUpdateRequest):
    updated = update_application_notes(application_id=application_id, notes=request.notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Application record not found.")
    return {"status": "success", "application": updated}


@app.get("/applications/{application_id}/history")
def get_application_history_endpoint(application_id: int):
    detail = get_application_detail(application_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Application record not found.")
    return {
        "application_id": application_id,
        "candidate_name": detail["candidate_name"],
        "status_history": detail.get("status_history", []),
    }


# ----------------------------------------------------------------------------
# CSV Export
# ----------------------------------------------------------------------------

@app.get("/jobs/{job_id}/export.csv")
def export_candidates_csv(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found.")

    candidates_data = list_applications_for_job(job_id=job_id, limit=1000)["candidates"]

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Candidate Name",
        "Email",
        "Phone",
        "Job Title",
        "Overall Score (%)",
        "Skill Score (%)",
        "Required Skill Coverage (%)",
        "Semantic Score (%)",
        "Matched Required Skills",
        "Missing Required Skills",
        "Matched Preferred Skills",
        "Missing Preferred Skills",
        "Experience Years Detected",
        "HR Status",
        "Application Date",
        "Original Filename",
        "HR Notes",
    ])

    for c in candidates_data:
        writer.writerow([
            c.get("candidate_name", ""),
            c.get("candidate_email", ""),
            c.get("candidate_phone", ""),
            job["title"],
            c.get("overall_score", ""),
            c.get("skill_score", ""),
            c.get("required_skill_coverage", ""),
            c.get("semantic_score", ""),
            "; ".join(c.get("matched_required_skills", [])),
            "; ".join(c.get("missing_required_skills", [])),
            "; ".join(c.get("matched_preferred_skills", [])),
            "; ".join(c.get("missing_preferred_skills", [])),
            c.get("experience_years_detected", ""),
            c.get("hr_status", ""),
            c.get("application_date", ""),
            c.get("original_filename", ""),
            c.get("notes", ""),
        ])

    csv_data = output.getvalue()
    safe_title = re.sub(r"[^A-Za-z0-9_-]", "_", job["title"].lower())
    filename = f"fairhire_candidates_{safe_title}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ----------------------------------------------------------------------------
# Fairness & Audit Endpoints
# ----------------------------------------------------------------------------

@app.get("/fairness/audit")
def fairness_audit_endpoint():
    return run_fairness_audit()


@app.get("/audit/events")
def audit_events_endpoint(limit: int = 50):
    return {"events": list_audit_events(limit=limit)}


# ----------------------------------------------------------------------------
# Demo Seeding Endpoint
# ----------------------------------------------------------------------------

@app.post("/demo/seed")
def seed_demo_data():
    """Seeds sample jobs and synthetic candidate resumes for complete HR evaluation."""
    # 1. Job 1: Junior Software Developer
    job1 = create_job(
        title="Junior Software Developer",
        department="Engineering",
        description=(
            "We are seeking an enthusiastic Junior Software Developer to build full-stack web applications. "
            "You will develop user-facing features, maintain APIs, and collaborate on data pipelines.\n\n"
            "Required Skills:\nPython, SQL, Git, React\n\n"
            "Preferred Skills:\nMachine Learning, REST API, Docker\n\n"
            "Responsibilities:\n"
            "- Develop and maintain web applications using Python and React.\n"
            "- Collaborate on relational databases and write clean SQL queries.\n"
            "- Participate in version control and code reviews using Git."
        ),
        responsibilities="Build web apps, manage databases, collaborate on git repos.",
        required_skills=["python", "sql", "git", "react"],
        preferred_skills=["machine learning", "rest api", "docker"],
        min_experience_years=0.0,
        education_requirement="Bachelor's in Computer Science or equivalent evidence",
        employment_type="Full-time",
        location="Hybrid / San Francisco, CA",
    )

    # 2. Job 2: Data Analyst
    job2 = create_job(
        title="Data Analyst",
        department="Data & Analytics",
        description=(
            "Join our business intelligence team as a Data Analyst. "
            "You will interpret complex datasets, build dashboards, and uncover operational insights.\n\n"
            "Required Skills:\nPython, SQL, Data Analysis, Pandas\n\n"
            "Preferred Skills:\nTableau, Machine Learning, Communication\n\n"
            "Responsibilities:\n"
            "- Clean and analyze structured datasets using Pandas and SQL.\n"
            "- Design executive dashboards and communicate analytical findings."
        ),
        responsibilities="Build dashboards, analyze data trends, create SQL reports.",
        required_skills=["python", "sql", "data analysis", "pandas"],
        preferred_skills=["tableau", "machine learning", "communication"],
        min_experience_years=1.0,
        education_requirement="Degree in Statistics, Analytics, or related field",
        employment_type="Full-time",
        location="Remote",
    )

    # Synthetic Candidate 1: Aarav Sharma (Strong Developer match, 81.82% baseline)
    aarav_text = """Aarav Sharma
Software Developer
aarav.sharma@example.com | +1 (555) 234-5678

Summary:
Motivated junior software engineer with solid foundations in Python, SQL, Git, and React. Passionate about building web applications and intelligent data solutions.

Skills:
Python, SQL, Git, React, Machine Learning

Experience:
Software Development Intern | Example Tech
June 2025 – August 2025
- Developed and maintained web features using React frontend and Python backend.
- Managed relational schema migrations with PostgreSQL and optimized complex SQL queries.
- Utilized Git for version control and pull request reviews.

Projects:
Housing Price Predictor
- Built a machine learning model to predict housing prices using Python and scikit-learn.
Full-Stack Web App
- Developed a web application with React and a REST API.

Education:
B.Tech in Computer Science, 2022 – 2026
"""

    # Synthetic Candidate 2: Priya Patel (Specialist Data Analyst)
    priya_text = """Priya Patel
Data Analyst & BI Specialist
priya.patel@example.com | +1 (555) 876-5432

Summary:
Detail-oriented analyst with 2 years of experience in data analysis, statistical modeling, and dashboard creation using Python, Pandas, and SQL.

Skills:
Python, SQL, Data Analysis, Pandas, NumPy, Tableau, Communication

Experience:
Junior Data Analyst | Insight Metrics
January 2024 – Present (1.5 years of experience)
- Built automated ETL workflows using Python and Pandas to analyze customer churn.
- Wrote high-performance SQL scripts across 10M+ transaction records.
- Designed interactive Tableau dashboards presenting KPIs to C-suite stakeholders.

Education:
B.S. in Data Science & Statistics, 2020 – 2024
"""

    # Synthetic Candidate 3: Marcus Vance (Senior Backend Engineer)
    marcus_text = """Marcus Vance
Backend Software Engineer
marcus.vance@example.com | +1 (555) 345-6789

Summary:
Backend developer with 4 years of experience focusing on scalable APIs, Docker containerization, and AWS cloud infrastructure.

Skills:
Python, SQL, Docker, AWS, REST API, Git, PostgreSQL, Linux

Experience:
Backend Engineer | CloudScale Systems
March 2022 – Present (3.5 years of experience)
- Designed resilient microservices using Python FastAPI and PostgreSQL.
- Containerized applications using Docker and orchestrated CI/CD pipelines to AWS ECS.
- Managed version control workflows across cross-functional teams with Git.

Education:
B.S. in Software Engineering, 2018 – 2022
"""

    # Synthetic Candidate 4: Elena Rostova (Frontend Specialist)
    elena_text = """Elena Rostova
Frontend UI/UX Engineer
elena.rostova@example.com | +1 (555) 901-2345

Summary:
Frontend developer with 2+ years of experience specializing in React, TypeScript, and modern responsive interfaces.

Skills:
React, TypeScript, JavaScript, HTML, CSS, Git, Communication, Teamwork

Experience:
Frontend Developer | Interface Lab
2023 – 2025 (2 years of experience)
- Developed modern web applications using React and TypeScript.
- Collaborated with UI designers and product managers using Git workflows.

Education:
B.A. in Interactive Media & Computing, 2019 – 2023
"""

    # Process candidates against Job 1 (Junior Software Developer)
    cands = [
        ("aarav_sharma_resume.txt", aarav_text),
        ("priya_patel_resume.txt", priya_text),
        ("marcus_vance_resume.txt", marcus_text),
        ("elena_rostova_resume.txt", elena_text),
    ]

    j1_results = []
    for fname, txt in cands:
        res = process_single_resume(txt.encode("utf-8"), fname, job1)
        j1_results.append(res)

    # Process candidates against Job 2 (Data Analyst) to demonstrate different scores for same resumes
    j2_results = []
    for fname, txt in cands:
        res = process_single_resume(txt.encode("utf-8"), fname, job2)
        j2_results.append(res)

    # Set some realistic HR statuses for onboarding demonstration
    if j1_results:
        update_application_status(
            j1_results[0]["application_id"],
            "shortlisted",
            note="Strong required-skills coverage (100%) and relevant internship background.",
        )
    if len(j1_results) > 1:
        update_application_status(
            j1_results[1]["application_id"],
            "under_review",
            note="Impressive data skills; review if suitable for backend/developer track.",
        )

    return {
        "status": "success",
        "message": "Demo data seeded successfully.",
        "jobs_created": [job1["title"], job2["title"]],
        "job1_candidates": len(j1_results),
        "job2_candidates": len(j2_results),
    }


# ----------------------------------------------------------------------------
# Legacy Single-Resume Analysis Endpoint (Preserved)
# ----------------------------------------------------------------------------

@app.post("/analyze")
async def analyze_candidate_legacy(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    filename = sanitize_filename(resume.filename or "resume.pdf")
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Please provide a job description.")

    contents = await resume.read()
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT resumes are supported.")

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        resume_path = workspace / f"resume{extension}"
        job_path = workspace / "job_description.txt"

        resume_path.write_bytes(contents)
        job_path.write_text(job_description, encoding="utf-8")

        parsed = parse_resume(resume_path)
        parsed_path = workspace / "parsed_resume.json"
        parsed_path.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")

        structured = analyze_resume(parsed_path)
        structured_path = workspace / "structured_resume.json"
        structured_path.write_text(json.dumps(structured, ensure_ascii=False), encoding="utf-8")

        from job_matcher import match_resume_to_job
        matching = match_resume_to_job(structured_path, job_path)

        semantic = calculate_semantic_similarity(
            {"parsed_resume": parsed, "structured_resume": structured},
            job_description,
        )

    return {
        "status": "success",
        "parsed_resume": parsed,
        "structured_resume": structured,
        "matching_result": matching,
        "semantic_result": semantic,
        "notice": (
            "Skill overlap and semantic similarity are separate measures. "
            "Neither establishes hiring probability or verified proficiency. Human review is required."
        ),
    }


@app.get("/jobs/{job_id}/screenings")
def get_job_screenings_legacy(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    candidates = list_applications_for_job(job_id=job_id, limit=200)["candidates"]
    return {
        "job": {"id": job["id"], "title": job["title"]},
        "count": len(candidates),
        "screenings": candidates,
    }
