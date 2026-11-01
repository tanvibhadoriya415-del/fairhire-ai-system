import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DATABASE_PATH = OUTPUTS_DIR / "fairhire.db"
STORAGE_DIR = OUTPUTS_DIR / "storage" / "resumes"


def get_connection():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Initializes tables and migrates any existing legacy columns/data."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        cursor = connection.cursor()

        # 1. Jobs Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                department TEXT NOT NULL DEFAULT 'Engineering',
                description TEXT NOT NULL,
                responsibilities TEXT NOT NULL DEFAULT '',
                required_skills TEXT NOT NULL DEFAULT '[]',
                preferred_skills TEXT NOT NULL DEFAULT '[]',
                min_experience_years REAL NOT NULL DEFAULT 0.0,
                education_requirement TEXT NOT NULL DEFAULT '',
                employment_type TEXT NOT NULL DEFAULT 'Full-time',
                location TEXT NOT NULL DEFAULT 'Remote / Hybrid',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Check and add any missing columns in jobs (for migration from legacy db)
        cursor.execute("PRAGMA table_info(jobs)")
        existing_job_cols = {row["name"] for row in cursor.fetchall()}
        job_column_defs = {
            "department": "TEXT NOT NULL DEFAULT 'Engineering'",
            "responsibilities": "TEXT NOT NULL DEFAULT ''",
            "required_skills": "TEXT NOT NULL DEFAULT '[]'",
            "preferred_skills": "TEXT NOT NULL DEFAULT '[]'",
            "min_experience_years": "REAL NOT NULL DEFAULT 0.0",
            "education_requirement": "TEXT NOT NULL DEFAULT ''",
            "employment_type": "TEXT NOT NULL DEFAULT 'Full-time'",
            "location": "TEXT NOT NULL DEFAULT 'Remote / Hybrid'",
            "status": "TEXT NOT NULL DEFAULT 'active'",
            "updated_at": "TEXT",
        }
        for col_name, col_def in job_column_defs.items():
            if col_name not in existing_job_cols:
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_def}")

        # 2. Candidates Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                headline TEXT,
                summary TEXT,
                skills TEXT NOT NULL DEFAULT '[]',
                education_text TEXT NOT NULL DEFAULT '',
                experience_text TEXT NOT NULL DEFAULT '',
                experience_years_detected REAL,
                projects_text TEXT NOT NULL DEFAULT '',
                certifications_text TEXT NOT NULL DEFAULT '',
                raw_text TEXT NOT NULL DEFAULT '',
                resume_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        cursor.execute("PRAGMA table_info(candidates)")
        existing_cand_cols = {row["name"] for row in cursor.fetchall()}
        cand_column_defs = {
            "name": "TEXT NOT NULL DEFAULT 'Candidate'",
            "email": "TEXT",
            "phone": "TEXT",
            "headline": "TEXT",
            "summary": "TEXT",
            "skills": "TEXT NOT NULL DEFAULT '[]'",
            "education_text": "TEXT NOT NULL DEFAULT ''",
            "experience_text": "TEXT NOT NULL DEFAULT ''",
            "experience_years_detected": "REAL",
            "projects_text": "TEXT NOT NULL DEFAULT ''",
            "certifications_text": "TEXT NOT NULL DEFAULT ''",
            "raw_text": "TEXT NOT NULL DEFAULT ''",
            "updated_at": "TEXT",
        }
        for col_name, col_def in cand_column_defs.items():
            if col_name not in existing_cand_cols:
                cursor.execute(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_def}")

        # 3. Applications Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filepath TEXT NOT NULL DEFAULT '',
                file_type TEXT NOT NULL DEFAULT 'pdf',
                processing_status TEXT NOT NULL DEFAULT 'completed',
                error_message TEXT,
                hr_status TEXT NOT NULL DEFAULT 'applied',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id, candidate_id),
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
            );
            """
        )

        # 4. Screening Results Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL UNIQUE,
                job_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                overall_score REAL NOT NULL,
                skill_score REAL NOT NULL,
                required_skill_coverage REAL NOT NULL,
                semantic_score REAL,
                matched_required_skills TEXT NOT NULL DEFAULT '[]',
                missing_required_skills TEXT NOT NULL DEFAULT '[]',
                matched_preferred_skills TEXT NOT NULL DEFAULT '[]',
                missing_preferred_skills TEXT NOT NULL DEFAULT '[]',
                evidence TEXT NOT NULL DEFAULT '{}',
                score_breakdown TEXT NOT NULL DEFAULT '{}',
                explanation TEXT NOT NULL DEFAULT '',
                warnings TEXT NOT NULL DEFAULT '[]',
                scoring_method TEXT NOT NULL DEFAULT 'weighted_skill_overlap_baseline',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE,
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
            );
            """
        )

        # 5. Status History / Audit Trail for Applications
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                note TEXT DEFAULT '',
                actor TEXT DEFAULT 'HR Recruiter',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
            );
            """
        )

        # 6. Audit Events Log
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                job_id INTEGER,
                application_id INTEGER,
                details TEXT NOT NULL DEFAULT '{}',
                actor TEXT DEFAULT 'HR Recruiter',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Migrate any legacy 'screenings' table data into 'applications' and 'screening_results'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='screenings'")
        if cursor.fetchone():
            cursor.execute("SELECT * FROM screenings")
            legacy_screenings = cursor.fetchall()
            for row in legacy_screenings:
                try:
                    r = dict(row)
                    job_id = r["job_id"]
                    candidate_id = r["candidate_id"]
                    skill_score = r.get("skill_score") or 0.0
                    semantic_score = r.get("semantic_score")
                    result_json = json.loads(r["result_json"]) if r.get("result_json") else {}

                    # Ensure application exists
                    cursor.execute(
                        "SELECT id FROM applications WHERE job_id = ? AND candidate_id = ?",
                        (job_id, candidate_id),
                    )
                    app_row = cursor.fetchone()
                    if not app_row:
                        cand_row = cursor.execute(
                            "SELECT filename FROM candidates WHERE id = ?",
                            (candidate_id,),
                        ).fetchone()
                        filename = cand_row["filename"] if cand_row and "filename" in cand_row.keys() else "resume.pdf"
                        ext = Path(filename).suffix.lstrip(".").lower() or "pdf"
                        cursor.execute(
                            """
                            INSERT INTO applications
                            (candidate_id, job_id, original_filename, file_type, processing_status, hr_status)
                            VALUES (?, ?, ?, ?, 'completed', 'applied')
                            """,
                            (candidate_id, job_id, filename, ext),
                        )
                        application_id = cursor.lastrowid
                    else:
                        application_id = app_row["id"]

                    # Ensure screening_results exists
                    cursor.execute(
                        "SELECT id FROM screening_results WHERE application_id = ?",
                        (application_id,),
                    )
                    if not cursor.fetchone():
                        matching = result_json.get("matching_result", {})
                        details = matching.get("matching_results", {})
                        matched_req = details.get("matched_required_skills", [])
                        missing_req = details.get("missing_required_skills", [])
                        matched_pref = details.get("matched_preferred_skills", [])
                        missing_pref = details.get("missing_preferred_skills", [])
                        total_req = len(matched_req) + len(missing_req)
                        coverage = round(100.0 * len(matched_req) / total_req, 2) if total_req else 100.0

                        cursor.execute(
                            """
                            INSERT INTO screening_results
                            (application_id, job_id, candidate_id, overall_score, skill_score,
                             required_skill_coverage, semantic_score, matched_required_skills,
                             missing_required_skills, matched_preferred_skills, missing_preferred_skills,
                             explanation, scoring_method)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                application_id,
                                job_id,
                                candidate_id,
                                skill_score,
                                skill_score,
                                coverage,
                                semantic_score,
                                json.dumps(matched_req),
                                json.dumps(missing_req),
                                json.dumps(matched_pref),
                                json.dumps(missing_pref),
                                details.get("explanation", "Baseline weighted skill match."),
                                details.get("scoring_method", "weighted_skill_overlap_baseline"),
                            ),
                        )
                except Exception:
                    pass

        connection.commit()


# ============================================================================
# Job Operations
# ============================================================================

def create_job(
    title: str,
    description: str,
    department: str = "Engineering",
    responsibilities: str = "",
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    min_experience_years: float = 0.0,
    education_requirement: str = "",
    employment_type: str = "Full-time",
    location: str = "Remote / Hybrid",
    status: str = "active",
) -> dict:
    title = (title or "").strip()
    description = (description or "").strip()

    if not title or not description:
        raise ValueError("Job title and description are required.")

    req_skills = [s.strip().lower() for s in (required_skills or []) if s.strip()]
    pref_skills = [s.strip().lower() for s in (preferred_skills or []) if s.strip()]

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO jobs
            (title, department, description, responsibilities, required_skills,
             preferred_skills, min_experience_years, education_requirement,
             employment_type, location, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                department.strip() or "Engineering",
                description,
                responsibilities.strip(),
                json.dumps(req_skills),
                json.dumps(pref_skills),
                float(min_experience_years or 0.0),
                education_requirement.strip(),
                employment_type.strip() or "Full-time",
                location.strip() or "Remote / Hybrid",
                status if status in ("active", "paused", "closed") else "active",
            ),
        )
        job_id = cursor.lastrowid
        connection.commit()

    record_audit_event("job_created", job_id=job_id, details={"title": title})
    return get_job(job_id)


def update_job(job_id: int, updates: dict) -> dict | None:
    job = get_job(job_id)
    if not job:
        return None

    allowed_fields = {
        "title", "department", "description", "responsibilities",
        "required_skills", "preferred_skills", "min_experience_years",
        "education_requirement", "employment_type", "location", "status",
    }

    set_clauses = []
    params = []

    for key, value in updates.items():
        if key in allowed_fields:
            if key in ("required_skills", "preferred_skills"):
                if isinstance(value, list):
                    value = json.dumps([str(s).strip().lower() for s in value if str(s).strip()])
                elif isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        value = json.dumps([str(s).strip().lower() for s in parsed if str(s).strip()])
                    except Exception:
                        items = [s.strip().lower() for s in value.split(",") if s.strip()]
                        value = json.dumps(items)
            elif key == "min_experience_years":
                value = float(value or 0.0)
            elif key == "status":
                if value not in ("active", "paused", "closed"):
                    value = "active"
            set_clauses.append(f"{key} = ?")
            params.append(value)

    if not set_clauses:
        return job

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.append(job_id)

    query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?"
    with get_connection() as connection:
        connection.execute(query, tuple(params))
        connection.commit()

    record_audit_event("job_updated", job_id=job_id, details=updates)
    return get_job(job_id)


def get_job(job_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT j.*,
                   COUNT(a.id) AS total_applications,
                   SUM(CASE WHEN a.processing_status = 'completed' THEN 1 ELSE 0 END) AS processed_applications,
                   SUM(CASE WHEN a.hr_status = 'shortlisted' THEN 1 ELSE 0 END) AS shortlisted_count,
                   AVG(sr.overall_score) AS average_score
            FROM jobs j
            LEFT JOIN applications a ON a.job_id = j.id
            LEFT JOIN screening_results sr ON sr.application_id = a.id
            WHERE j.id = ?
            GROUP BY j.id
            """,
            (job_id,),
        ).fetchone()

    if not row:
        return None

    item = dict(row)
    item["required_skills"] = json.loads(item["required_skills"] or "[]")
    item["preferred_skills"] = json.loads(item["preferred_skills"] or "[]")
    item["average_score"] = round(item["average_score"], 2) if item.get("average_score") is not None else None
    return item


def list_jobs(search: str | None = None, status: str | None = None) -> list[dict]:
    query = """
        SELECT j.*,
               COUNT(a.id) AS total_applications,
               SUM(CASE WHEN a.processing_status = 'completed' THEN 1 ELSE 0 END) AS processed_applications,
               SUM(CASE WHEN a.hr_status = 'shortlisted' THEN 1 ELSE 0 END) AS shortlisted_count,
               AVG(sr.overall_score) AS average_score
        FROM jobs j
        LEFT JOIN applications a ON a.job_id = j.id
        LEFT JOIN screening_results sr ON sr.application_id = a.id
        WHERE 1=1
    """
    params = []

    if status and status != "all":
        query += " AND j.status = ?"
        params.append(status)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query += " AND (j.title LIKE ? OR j.department LIKE ? OR j.description LIKE ?)"
        params.extend([term, term, term])

    query += " GROUP BY j.id ORDER BY j.id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, tuple(params)).fetchall()

    results = []
    for row in rows:
        item = dict(row)
        item["required_skills"] = json.loads(item["required_skills"] or "[]")
        item["preferred_skills"] = json.loads(item["preferred_skills"] or "[]")
        item["average_score"] = round(item["average_score"], 2) if item.get("average_score") is not None else None
        results.append(item)

    return results


# ============================================================================
# Candidate & Application Operations
# ============================================================================

def save_or_update_candidate(
    name: str,
    resume_hash: str,
    raw_text: str,
    skills: list[str],
    email: str | None = None,
    phone: str | None = None,
    headline: str | None = None,
    summary: str | None = None,
    education_text: str = "",
    experience_text: str = "",
    experience_years_detected: float | None = None,
    projects_text: str = "",
    certifications_text: str = "",
    filename: str = "resume.pdf",
) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM candidates WHERE resume_hash = ?", (resume_hash,))
        existing = cursor.fetchone()

        cursor.execute("PRAGMA table_info(candidates)")
        cols = {row["name"] for row in cursor.fetchall()}

        parsed_json = json.dumps({"name": name, "skills": skills, "text": raw_text[:2000]})
        structured_json = json.dumps({"name": name, "skills": skills, "education": education_text, "experience": experience_text})

        if existing:
            candidate_id = existing["id"]
            update_sql = """
                UPDATE candidates
                SET name = ?, email = ?, phone = ?, headline = ?, summary = ?,
                    skills = ?, education_text = ?, experience_text = ?,
                    experience_years_detected = ?, projects_text = ?,
                    certifications_text = ?, raw_text = ?, updated_at = CURRENT_TIMESTAMP
            """
            params = [
                name or "Candidate", email, phone, headline, summary,
                json.dumps(skills), education_text, experience_text,
                experience_years_detected, projects_text, certifications_text,
                raw_text,
            ]
            if "filename" in cols:
                update_sql += ", filename = ?"
                params.append(filename)
            if "parsed_resume" in cols:
                update_sql += ", parsed_resume = ?"
                params.append(parsed_json)
            if "structured_resume" in cols:
                update_sql += ", structured_resume = ?"
                params.append(structured_json)

            update_sql += " WHERE id = ?"
            params.append(candidate_id)
            cursor.execute(update_sql, tuple(params))
        else:
            col_list = [
                "name", "email", "phone", "headline", "summary",
                "skills", "education_text", "experience_text",
                "experience_years_detected", "projects_text",
                "certifications_text", "raw_text", "resume_hash",
            ]
            val_list = [
                name or "Candidate", email, phone, headline, summary,
                json.dumps(skills), education_text, experience_text,
                experience_years_detected, projects_text,
                certifications_text, raw_text, resume_hash,
            ]
            if "filename" in cols:
                col_list.append("filename")
                val_list.append(filename)
            if "parsed_resume" in cols:
                col_list.append("parsed_resume")
                val_list.append(parsed_json)
            if "structured_resume" in cols:
                col_list.append("structured_resume")
                val_list.append(structured_json)

            placeholders = ", ".join(["?"] * len(col_list))
            insert_sql = f"INSERT INTO candidates ({', '.join(col_list)}) VALUES ({placeholders})"
            cursor.execute(insert_sql, tuple(val_list))
            candidate_id = cursor.lastrowid

        connection.commit()
    return candidate_id


def create_or_get_application(
    candidate_id: int,
    job_id: int,
    original_filename: str,
    stored_filepath: str,
    file_type: str,
    processing_status: str = "completed",
    error_message: str | None = None,
) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM applications WHERE job_id = ? AND candidate_id = ?",
            (job_id, candidate_id),
        )
        existing = cursor.fetchone()

        if existing:
            app_id = existing["id"]
            cursor.execute(
                """
                UPDATE applications
                SET original_filename = ?, stored_filepath = ?, file_type = ?,
                    processing_status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (original_filename, stored_filepath, file_type, processing_status, error_message, app_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO applications
                (candidate_id, job_id, original_filename, stored_filepath, file_type, processing_status, error_message, hr_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'applied')
                """,
                (candidate_id, job_id, original_filename, stored_filepath, file_type, processing_status, error_message),
            )
            app_id = cursor.lastrowid
            # Record initial status in history
            cursor.execute(
                """
                INSERT INTO status_history (application_id, previous_status, new_status, note)
                VALUES (?, NULL, 'applied', 'Application created via screening upload')
                """,
                (app_id,),
            )

        connection.commit()
    return app_id


def save_screening_result(
    application_id: int,
    job_id: int,
    candidate_id: int,
    overall_score: float,
    skill_score: float,
    required_skill_coverage: float,
    semantic_score: float | None,
    matched_required_skills: list[str],
    missing_required_skills: list[str],
    matched_preferred_skills: list[str],
    missing_preferred_skills: list[str],
    evidence: dict,
    score_breakdown: dict,
    explanation: str,
    warnings: list[str],
    scoring_method: str = "weighted_skill_overlap_baseline",
) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO screening_results
            (application_id, job_id, candidate_id, overall_score, skill_score,
             required_skill_coverage, semantic_score, matched_required_skills,
             missing_required_skills, matched_preferred_skills, missing_preferred_skills,
             evidence, score_breakdown, explanation, warnings, scoring_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(application_id) DO UPDATE SET
                overall_score = excluded.overall_score,
                skill_score = excluded.skill_score,
                required_skill_coverage = excluded.required_skill_coverage,
                semantic_score = excluded.semantic_score,
                matched_required_skills = excluded.matched_required_skills,
                missing_required_skills = excluded.missing_required_skills,
                matched_preferred_skills = excluded.matched_preferred_skills,
                missing_preferred_skills = excluded.missing_preferred_skills,
                evidence = excluded.evidence,
                score_breakdown = excluded.score_breakdown,
                explanation = excluded.explanation,
                warnings = excluded.warnings,
                scoring_method = excluded.scoring_method,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                application_id,
                job_id,
                candidate_id,
                float(overall_score),
                float(skill_score),
                float(required_skill_coverage),
                float(semantic_score) if semantic_score is not None else None,
                json.dumps(matched_required_skills),
                json.dumps(missing_required_skills),
                json.dumps(matched_preferred_skills),
                json.dumps(missing_preferred_skills),
                json.dumps(evidence),
                json.dumps(score_breakdown),
                explanation,
                json.dumps(warnings),
                scoring_method,
            ),
        )
        result_id = cursor.lastrowid
        connection.commit()
    return result_id


# ============================================================================
# Application Queries, Filtering & Sorting
# ============================================================================

def list_applications_for_job(
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
    sort_by: str = "score_desc",
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Returns filtered and sorted candidates/applications for a job."""
    query = """
        SELECT
            a.id AS application_id,
            a.candidate_id,
            a.job_id,
            a.original_filename,
            a.stored_filepath,
            a.file_type,
            a.processing_status,
            a.error_message,
            a.hr_status,
            a.notes,
            a.created_at AS application_date,
            a.updated_at AS application_updated_at,
            c.name AS candidate_name,
            c.email AS candidate_email,
            c.phone AS candidate_phone,
            c.headline AS candidate_headline,
            c.skills AS candidate_skills,
            c.experience_years_detected,
            c.education_text,
            c.experience_text,
            sr.overall_score,
            sr.skill_score,
            sr.required_skill_coverage,
            sr.semantic_score,
            sr.matched_required_skills,
            sr.missing_required_skills,
            sr.matched_preferred_skills,
            sr.missing_preferred_skills,
            sr.evidence,
            sr.score_breakdown,
            sr.explanation,
            sr.warnings,
            sr.scoring_method,
            j.title AS job_title
        FROM applications a
        JOIN candidates c ON c.id = a.candidate_id
        JOIN jobs j ON j.id = a.job_id
        LEFT JOIN screening_results sr ON sr.application_id = a.id
        WHERE a.job_id = ?
    """
    params = [job_id]

    if hr_status and hr_status != "all":
        query += " AND a.hr_status = ?"
        params.append(hr_status)

    if processing_status and processing_status != "all":
        query += " AND a.processing_status = ?"
        params.append(processing_status)

    if min_score is not None:
        query += " AND sr.overall_score >= ?"
        params.append(float(min_score))

    if max_score is not None:
        query += " AND sr.overall_score <= ?"
        params.append(float(max_score))

    if min_experience is not None:
        query += " AND c.experience_years_detected >= ?"
        params.append(float(min_experience))

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query += """
            AND (
                LOWER(c.name) LIKE ? OR
                LOWER(c.email) LIKE ? OR
                LOWER(c.skills) LIKE ? OR
                LOWER(c.raw_text) LIKE ? OR
                LOWER(a.original_filename) LIKE ?
            )
        """
        params.extend([term, term, term, term, term])

    if matched_skill and matched_skill.strip():
        skill_term = f"%\"{matched_skill.strip().lower()}\"%"
        query += " AND (sr.matched_required_skills LIKE ? OR sr.matched_preferred_skills LIKE ?)"
        params.extend([skill_term, skill_term])

    if missing_skill and missing_skill.strip():
        skill_term = f"%\"{missing_skill.strip().lower()}\"%"
        query += " AND (sr.missing_required_skills LIKE ? OR sr.missing_preferred_skills LIKE ?)"
        params.extend([skill_term, skill_term])

    if required_skill and required_skill.strip():
        skill_term = f"%\"{required_skill.strip().lower()}\"%"
        query += " AND sr.matched_required_skills LIKE ?"
        params.append(skill_term)

    if preferred_skill and preferred_skill.strip():
        skill_term = f"%\"{preferred_skill.strip().lower()}\"%"
        query += " AND sr.matched_preferred_skills LIKE ?"
        params.append(skill_term)

    # Sorting
    sort_mapping = {
        "score_desc": "CASE WHEN sr.overall_score IS NULL THEN 1 ELSE 0 END, sr.overall_score DESC, a.id DESC",
        "score_asc": "CASE WHEN sr.overall_score IS NULL THEN 1 ELSE 0 END, sr.overall_score ASC, a.id DESC",
        "coverage_desc": "CASE WHEN sr.required_skill_coverage IS NULL THEN 1 ELSE 0 END, sr.required_skill_coverage DESC, a.id DESC",
        "coverage_asc": "CASE WHEN sr.required_skill_coverage IS NULL THEN 1 ELSE 0 END, sr.required_skill_coverage ASC, a.id DESC",
        "experience_desc": "CASE WHEN c.experience_years_detected IS NULL THEN 1 ELSE 0 END, c.experience_years_detected DESC, a.id DESC",
        "experience_asc": "CASE WHEN c.experience_years_detected IS NULL THEN 1 ELSE 0 END, c.experience_years_detected ASC, a.id DESC",
        "date_desc": "a.created_at DESC",
        "date_asc": "a.created_at ASC",
        "name_asc": "c.name ASC",
        "name_desc": "c.name DESC",
    }
    order_by_clause = sort_mapping.get(sort_by, sort_mapping["score_desc"])
    query += f" ORDER BY {order_by_clause}"

    # Count total matching
    count_query = f"SELECT COUNT(*) FROM ({query})"
    with get_connection() as connection:
        total_count = connection.execute(count_query, tuple(params)).fetchone()[0]

        # Apply pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = connection.execute(query, tuple(params)).fetchall()

    results = []
    for row in rows:
        item = dict(row)
        item["candidate_skills"] = json.loads(item["candidate_skills"] or "[]")
        item["matched_required_skills"] = json.loads(item["matched_required_skills"] or "[]")
        item["missing_required_skills"] = json.loads(item["missing_required_skills"] or "[]")
        item["matched_preferred_skills"] = json.loads(item["matched_preferred_skills"] or "[]")
        item["missing_preferred_skills"] = json.loads(item["missing_preferred_skills"] or "[]")
        item["evidence"] = json.loads(item["evidence"] or "{}")
        item["score_breakdown"] = json.loads(item["score_breakdown"] or "{}")
        item["warnings"] = json.loads(item["warnings"] or "[]")
        results.append(item)

    return {
        "total": total_count,
        "count": len(results),
        "limit": limit,
        "offset": offset,
        "candidates": results,
    }


def get_application_detail(application_id: int) -> dict | None:
    query = """
        SELECT
            a.id AS application_id,
            a.candidate_id,
            a.job_id,
            a.original_filename,
            a.stored_filepath,
            a.file_type,
            a.processing_status,
            a.error_message,
            a.hr_status,
            a.notes,
            a.created_at AS application_date,
            a.updated_at AS application_updated_at,
            c.name AS candidate_name,
            c.email AS candidate_email,
            c.phone AS candidate_phone,
            c.headline AS candidate_headline,
            c.summary AS candidate_summary,
            c.skills AS candidate_skills,
            c.education_text,
            c.experience_text,
            c.experience_years_detected,
            c.projects_text,
            c.certifications_text,
            c.raw_text,
            c.resume_hash,
            j.title AS job_title,
            j.department AS job_department,
            j.description AS job_description,
            j.responsibilities AS job_responsibilities,
            j.required_skills AS job_required_skills,
            j.preferred_skills AS job_preferred_skills,
            j.min_experience_years AS job_min_experience,
            sr.overall_score,
            sr.skill_score,
            sr.required_skill_coverage,
            sr.semantic_score,
            sr.matched_required_skills,
            sr.missing_required_skills,
            sr.matched_preferred_skills,
            sr.missing_preferred_skills,
            sr.evidence,
            sr.score_breakdown,
            sr.explanation,
            sr.warnings,
            sr.scoring_method,
            sr.created_at AS screening_timestamp
        FROM applications a
        JOIN candidates c ON c.id = a.candidate_id
        JOIN jobs j ON j.id = a.job_id
        LEFT JOIN screening_results sr ON sr.application_id = a.id
        WHERE a.id = ?
    """
    with get_connection() as connection:
        row = connection.execute(query, (application_id,)).fetchone()
        if not row:
            return None

        history_rows = connection.execute(
            """
            SELECT * FROM status_history
            WHERE application_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (application_id,),
        ).fetchall()

    item = dict(row)
    item["candidate_skills"] = json.loads(item["candidate_skills"] or "[]")
    item["job_required_skills"] = json.loads(item["job_required_skills"] or "[]")
    item["job_preferred_skills"] = json.loads(item["job_preferred_skills"] or "[]")
    item["matched_required_skills"] = json.loads(item["matched_required_skills"] or "[]")
    item["missing_required_skills"] = json.loads(item["missing_required_skills"] or "[]")
    item["matched_preferred_skills"] = json.loads(item["matched_preferred_skills"] or "[]")
    item["missing_preferred_skills"] = json.loads(item["missing_preferred_skills"] or "[]")
    item["evidence"] = json.loads(item["evidence"] or "{}")
    item["score_breakdown"] = json.loads(item["score_breakdown"] or "{}")
    item["warnings"] = json.loads(item["warnings"] or "[]")
    item["status_history"] = [dict(h) for h in history_rows]

    return item


def update_application_status(
    application_id: int,
    new_status: str,
    note: str = "",
    actor: str = "HR Recruiter",
) -> dict | None:
    valid_statuses = {
        "applied", "under_review", "shortlisted",
        "interview_scheduled", "offer_pending", "rejected"
    }
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'. Allowed: {', '.join(sorted(valid_statuses))}")

    with get_connection() as connection:
        cursor = connection.cursor()
        current = cursor.execute(
            "SELECT hr_status, job_id, candidate_id FROM applications WHERE id = ?",
            (application_id,),
        ).fetchone()

        if not current:
            return None

        prev_status = current["hr_status"]
        if prev_status == new_status and not note:
            return get_application_detail(application_id)

        cursor.execute(
            """
            UPDATE applications
            SET hr_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, application_id),
        )

        cursor.execute(
            """
            INSERT INTO status_history
            (application_id, previous_status, new_status, note, actor)
            VALUES (?, ?, ?, ?, ?)
            """,
            (application_id, prev_status, new_status, note.strip(), actor),
        )

        connection.commit()

    record_audit_event(
        "status_changed",
        job_id=current["job_id"],
        application_id=application_id,
        details={"previous": prev_status, "new": new_status, "note": note},
        actor=actor,
    )

    return get_application_detail(application_id)


def update_application_notes(application_id: int, notes: str) -> dict | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        current = cursor.execute(
            "SELECT id, job_id FROM applications WHERE id = ?",
            (application_id,),
        ).fetchone()

        if not current:
            return None

        cursor.execute(
            """
            UPDATE applications
            SET notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (notes, application_id),
        )
        connection.commit()

    record_audit_event(
        "note_updated",
        job_id=current["job_id"],
        application_id=application_id,
        details={"notes_length": len(notes)},
    )

    return get_application_detail(application_id)


# ============================================================================
# Dashboard Statistics & Audit Events
# ============================================================================

def get_dashboard_stats() -> dict:
    with get_connection() as connection:
        total_jobs = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        active_jobs = connection.execute("SELECT COUNT(*) FROM jobs WHERE status = 'active'").fetchone()[0]
        total_applications = connection.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        processed_resumes = connection.execute(
            "SELECT COUNT(*) FROM applications WHERE processing_status = 'completed'"
        ).fetchone()[0]
        awaiting_review = connection.execute(
            "SELECT COUNT(*) FROM applications WHERE hr_status IN ('applied', 'under_review')"
        ).fetchone()[0]
        shortlisted = connection.execute(
            "SELECT COUNT(*) FROM applications WHERE hr_status = 'shortlisted'"
        ).fetchone()[0]
        interviews_scheduled = connection.execute(
            "SELECT COUNT(*) FROM applications WHERE hr_status = 'interview_scheduled'"
        ).fetchone()[0]
        failed_screenings = connection.execute(
            "SELECT COUNT(*) FROM applications WHERE processing_status = 'failed'"
        ).fetchone()[0]

        recent_jobs = connection.execute(
            """
            SELECT j.id, j.title, j.department, j.status, j.created_at,
                   COUNT(a.id) AS candidate_count
            FROM jobs j
            LEFT JOIN applications a ON a.job_id = j.id
            GROUP BY j.id
            ORDER BY j.created_at DESC
            LIMIT 5
            """
        ).fetchall()

        recent_screenings = connection.execute(
            """
            SELECT a.id AS application_id, c.name AS candidate_name, j.title AS job_title,
                   sr.overall_score, a.hr_status, a.created_at
            FROM applications a
            JOIN candidates c ON c.id = a.candidate_id
            JOIN jobs j ON j.id = a.job_id
            LEFT JOIN screening_results sr ON sr.application_id = a.id
            WHERE a.processing_status = 'completed'
            ORDER BY a.created_at DESC
            LIMIT 6
            """
        ).fetchall()

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "processed_resumes": processed_resumes,
        "awaiting_review": awaiting_review,
        "shortlisted_candidates": shortlisted,
        "interviews_scheduled": interviews_scheduled,
        "screening_failures": failed_screenings,
        "recent_jobs": [dict(r) for r in recent_jobs],
        "recent_screenings": [dict(r) for r in recent_screenings],
    }


def record_audit_event(
    event_type: str,
    job_id: int | None = None,
    application_id: int | None = None,
    details: dict | None = None,
    actor: str = "HR Recruiter",
):
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (event_type, job_id, application_id, details, actor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_type, job_id, application_id, json.dumps(details or {}), actor),
            )
            connection.commit()
    except Exception:
        pass


def list_audit_events(limit: int = 50) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT ae.*, j.title AS job_title
            FROM audit_events ae
            LEFT JOIN jobs j ON j.id = ae.job_id
            ORDER BY ae.created_at DESC, ae.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        item = dict(row)
        item["details"] = json.loads(item["details"] or "{}")
        results.append(item)
    return results


# Initialize schema upon module load
initialize_database()
