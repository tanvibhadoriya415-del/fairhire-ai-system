# FairHire AI
## AI-Based Explainable and Bias-Aware Resume Screening System

> **Smarter screening. Clearer decisions. Fairer hiring.**

FairHire AI is a full-stack, enterprise-grade HR SaaS platform engineered to solve the bottleneck of manual resume screening across multiple job openings. It combines transparent, explainable skill matching, dense neural and TF-IDF semantic relevance, responsible-AI bias guardrails, and persistent SQLite storage with a modern React recruitment interface.

---

## 1. Key Features

- **Multi-Job Management**: Create and manage multiple active, paused, or closed job openings. Paste full job descriptions and use the AI requirement parser to auto-extract and review required vs. preferred skills.
- **Explainable Matching Engine**: Deterministic weighted skill-overlap scoring (Required skills = Weight 2, Preferred skills = Weight 1) with individual required-skill coverage percentages and evidence excerpts.
- **Dual Semantic Relevance**: SentenceTransformers dense embeddings (`all-MiniLM-L6-v2`) with a fast, zero-network fallback to `scikit-learn` TF-IDF cosine similarity.
- **Batch Resume Processing**: Drag-and-drop or select multiple resumes at once across PDF, DOCX, and TXT formats (up to 10 MB per file) with safe hashed server-side storage.
- **Candidate Explorer**:
  - Filter by job, match score ranges, required skills, preferred skills, matched skills, missing skills, HR stage, processing status, and experience.
  - Sort by match score, required coverage, experience, application date, or candidate name (ascending/descending).
  - Search across candidate names, emails, skills, and full resume text.
- **Candidate Profile & Evidence Drawer**:
  - Inspect structured resume sections (Summary, Skills, Work Experience, Education, Projects).
  - Review exact supporting excerpts for every matched skill.
  - Clearly distinguish between *"Skill not detected"* vs. *"Candidate lacks skill"*.
  - View full raw extracted resume text.
- **Human-in-the-Loop HR Decisions**:
  - Update candidate stages (`Applied`, `Under Review`, `Shortlisted`, `Interview Scheduled`, `Offer Pending`, `Rejected`).
  - Add and edit private internal HR notes.
  - Complete immutable status change audit trail with timestamps and reviewer notes.
- **Re-Screening Workflow**: When job requirements or descriptions are updated, re-screen all existing applicants with one click.
- **CSV Export**: Export filtered candidate screening results, contact info, scores, and HR notes to CSV.
- **Responsible-AI Guardrails & Bias Audit**:
  - Strict exclusion of 10+ sensitive characteristics (gender, race, ethnicity, religion, caste, disability, marital status, photo, age/graduation year proxies, zip code/address).
  - Controlled synthetic score consistency audit tool demonstrating zero score gap across equivalent demographic labels.
  - Explicit system limitations and human oversight disclaimer.
- **1-Click Demo Data**: Instant onboarding button to seed realistic synthetic jobs and candidate resumes (Aarav Sharma, Priya Patel, Marcus Vance, Elena Rostova).

---

## 2. Technology Stack

- **Frontend**: React 19, Vite 8, Modern CSS Variables Design System, Custom SVG Icons (Lucide-inspired).
- **Backend**: Python 3.11, FastAPI, Pydantic v2, Uvicorn.
- **AI & Text Extraction**:
  - `pypdf` for PDF parsing.
  - `python-docx` for Word DOCX extraction.
  - Standard UTF-8 decoding for TXT files.
  - `sentence-transformers` (`all-MiniLM-L6-v2`) & `scikit-learn` TF-IDF cosine similarity.
  - Regex and boundary heuristics for evidence excerpt extraction.
- **Database & Storage**:
  - Local SQLite database (`outputs/fairhire.db`) with Foreign Keys, indexed searches, and safe schema migrations.
  - Dedicated file storage in `outputs/storage/resumes/`.
- **Testing**: `pytest` test suite with 22 comprehensive unit and integration tests.

---

## 3. Project Directory Structure

```text
Cornerstone_project/
├── backend/
│   ├── database.py             # SQLite schema, migrations, CRUD, and audit logs
│   ├── fairness_audit.py       # Controlled synthetic demographic consistency test
│   ├── main.py                 # FastAPI application routes, batch screening, CSV export
│   └── semantic_matcher.py     # SentenceTransformer & TF-IDF cosine similarity
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Icons.jsx                 # Custom SVG icons
│   │   │   └── CandidateDetailDrawer.jsx # Candidate profile drawer with evidence & actions
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx         # Live metrics, recent activity, quick actions
│   │   │   ├── JobManagementPage.jsx     # Job creation, requirement parsing, pipeline counts
│   │   │   ├── ResumeUploadPage.jsx      # Batch file upload, queue, screening progress
│   │   │   ├── CandidateExplorerPage.jsx # Filterable/sortable table, search, CSV export
│   │   │   ├── ExplainabilityFairnessPage.jsx # Scoring formula, bias audit, limitations
│   │   │   └── AuditHistoryPage.jsx      # System compliance and status change audit log
│   │   ├── services/
│   │   │   └── api.js                    # Unified REST client
│   │   ├── App.jsx                       # Main application shell and routing
│   │   ├── App.css                       # Enterprise navy/indigo design system
│   │   └── main.jsx                      # Vite entry point
│   ├── package.json
│   └── vite.config.js                    # Proxy config to FastAPI (:8000)
├── datasets/
│   └── synthetic_resumes/                # Synthetic test candidates (.txt, .docx)
├── outputs/
│   ├── fairhire.db                       # Persistent SQLite database
│   └── storage/resumes/                  # Safe server-side uploaded resume storage
├── tests/
│   ├── test_analyzer.py                  # Tests for section detection, skills & profile
│   ├── test_api.py                       # Tests for FastAPI endpoints, jobs, batch screen, CSV
│   ├── test_matcher.py                   # Tests for weighted matching, baseline 81.82%, coverage
│   └── test_parser.py                    # Tests for PDF, DOCX, TXT, and error handling
├── job_matcher.py                        # Core weighted matching baseline engine
├── resume_analyzer.py                    # Structured information & evidence extractor
├── resume_parser.py                      # Multi-format document text extractor
├── requirements.txt                      # Python dependencies manifest
├── .env.example                          # Environment variables template
└── README.md                             # Comprehensive documentation
```

---

## 4. Prerequisites

- **OS**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.11+
- **Node.js**: Version 18+ and `npm`

---

## 5. Quick Start (Windows PowerShell)

Open PowerShell and navigate to the project directory:

```powershell
Set-Location "C:\Users\91930\Desktop\Cornerstone_project"
```

### Step 1: Virtual Environment & Python Dependencies

If the virtual environment is not already active, activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

### Step 2: Frontend Dependencies

```powershell
cd frontend
npm install
cd ..
```

### Step 3: Run the Backend Server

Start the FastAPI application with Uvicorn:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### Step 4: Run the Frontend Development Server

In a second PowerShell terminal:

```powershell
Set-Location "C:\Users\91930\Desktop\Cornerstone_project\frontend"
npm run dev
```

Open your browser at:

👉 **`http://localhost:5173`**

*(Requests to `/api/*` are automatically proxied to `http://127.0.0.1:8000` by Vite).*

---

## 6. How to Use FairHire AI (Recruiter Walkthrough)

1. **Dashboard Overview**:
   - Open `http://localhost:5173`.
   - Inspect live metrics (Active Job Openings, Total Applications, Awaiting HR Review, Shortlisted).
   - If starting fresh, click **"Load Sample HR Data"** in the top banner or sidebar to immediately populate realistic sample jobs and applicants.
2. **Create or Manage Job Openings**:
   - Navigate to **"Job Openings"** in the sidebar.
   - Click **"Create Job Opening"**.
   - Enter a title (e.g. *Junior Software Developer*), department, and paste a job description.
   - Click **"Auto-Extract Skills from Description"** to automatically populate recommended Required and Preferred skills, then review or add skills using the chips editor.
   - Set status to *Active* and save.
3. **Upload and Screen Resumes**:
   - Navigate to **"Screen Resumes"**.
   - Select the target job opening from the dropdown. Review the stated Required and Preferred skills.
   - Drag and drop or browse for resumes (PDF, DOCX, or TXT). Multiple files can be uploaded simultaneously.
   - Click **"Start Screening Batch"**.
   - Monitor the per-file processing state. Inspect the completion summary.
4. **Explore, Filter & Sort Candidates**:
   - Navigate to **"Candidate Explorer"**.
   - Select the job opening. Notice how candidates receive job-specific scores.
   - Use the **Search Bar** to search across candidate names, emails, skills, or resume text.
   - Open **Filters** to filter by minimum match score (e.g. 60%), must-have skills (e.g. `python`), or HR stage (`Under Review`, `Shortlisted`).
   - Use the **Sort** dropdown to sort by Highest Match Score, Highest Required Coverage, Most Relevant Experience, or Candidate Name.
   - Click **"Export CSV"** to download the candidate list and scores.
5. **Inspect Candidate Profile & Evidence**:
   - Click **"Profile"** next to any candidate in the table to open the Candidate Profile Drawer.
   - View **Matched Required Skills**: Click on any skill to expand and inspect the exact resume excerpt supporting the match!
   - Review **Required Skills Not Detected**: Clearly distinguished from "candidate lacks skill".
   - Review the mathematical **Score Breakdown** (Required: 2 pts, Preferred: 1 pt).
   - Switch tabs to view **Extracted Resume** sections or the raw resume text preview.
6. **Record HR Decisions**:
   - In the candidate drawer, switch to **"HR Actions & Notes"**.
   - Click **"Shortlist"**, **"Interview"**, or **"Reject"**.
   - Enter an optional decision reason in the note field.
   - Add private internal HR notes and click **"Save HR Notes"**.
   - Switch to the **"Status History"** tab to view the complete audit trail.
7. **Audit & Explainability**:
   - Navigate to **"Explainability & Bias"** in the sidebar.
   - Review the transparent scoring formula and list of 10+ excluded demographic features.
   - Click **"Run Live Fairness Audit"** to execute a controlled demographic consistency evaluation.
   - Navigate to **"Audit Trail"** to inspect system logs.

---

## 7. Scoring Formula & Explainability

FairHire AI uses a deterministic, explainable scoring baseline:

$$\text{Match Score} = \frac{2 \times |\text{Matched Required}| + 1 \times |\text{Matched Preferred}|}{2 \times |\text{Total Required}| + 1 \times |\text{Total Preferred}|} \times 100\%$$

$$\text{Required Coverage} = \frac{|\text{Matched Required}|}{|\text{Total Required}|} \times 100\%$$

### Example: Aarav Sharma against Junior Software Developer
- **Job Requirements**: Required: `Python`, `SQL`, `Git`, `React` (4 skills). Preferred: `Machine Learning`, `REST API`, `Docker` (3 skills).
- **Candidate Skills**: `Git`, `Python`, `React`, `SQL`, `Machine Learning`.
- **Calculation**:
  - Matched Required: 4 skills $\times 2$ points = 8 points.
  - Matched Preferred: 1 skill (ML) $\times 1$ point = 1 point.
  - Total Points Earned: 9 points.
  - Total Points Possible: $(4 \times 2) + (3 \times 1) = 11$ points.
  - Match Score: $\frac{9}{11} \times 100\% = 81.82\%$.
  - Required Coverage: $\frac{4}{4} \times 100\% = 100.0\%$.

### Multi-Job Differential Scoring
If Aarav Sharma is evaluated against **Data Analyst** (Required: `Python`, `SQL`, `Data Analysis`, `Pandas`):
- Required matched: 2 (`Python`, `SQL`) out of 4.
- Required coverage drops to $50.0\%$, and match score becomes $45.45\%$.
This proves candidate scores are strictly job-specific.

---

## 8. Responsible AI & Fairness Safeguards

1. **Demographic Exclusion**: No demographic variables (gender, race, religion, caste, disability, marital status, photograph, age, address) are included in the scoring formula or model features.
2. **Deterministic Alignment**: Scores measure textual evidence alignment against explicit job criteria, not innate candidate quality.
3. **No Automated Disqualification**: The system never automatically rejects applicants based on thresholds; all stage changes require human recruiter approval.
4. **Unknown Experience**: Missing or indeterminate experience is recorded as `Unknown` rather than penalized as `0.0` years.
5. **Auditing**: Live controlled synthetic score consistency checks test demographic neutrality across equivalent candidate records.

---

## 9. Running Automated Tests

Run the backend pytest suite:

```powershell
Set-Location "C:\Users\91930\Desktop\Cornerstone_project"
.\.venv\Scripts\Activate.ps1
pytest tests -v
```

All 22 tests cover:
- Document extraction across PDF, DOCX, and TXT.
- Section identification, contact info extraction, and evidence context extraction.
- Deterministic weighted scoring and the 81.82% Aarav baseline.
- Multi-job score differentiation.
- Complete FastAPI CRUD, screening, filtering, sorting, status updates, notes, and CSV export.

---

## 10. Security & Privacy Safeguards

- Uploaded files are restricted to PDF, DOCX, and TXT with a 10 MB limit.
- Resumes are stored with SHA256 hashed server-side filenames outside public static folders.
- Path traversal protections prevent arbitrary filesystem writes.
- Sanitized database queries prevent SQL injection.
- CORS is restricted to local development origins.

---

## 11. Troubleshooting

- **PowerShell Execution Policy Error**: If `Activate.ps1` gives an execution policy error, run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
- **Port Conflict on 8000**: Run Uvicorn on another port with `--port 8001`, and update `target` in `frontend/vite.config.js`.
- **EPERM during npm install**: Transient on Windows; run the command again in PowerShell.

---

## 12. License & Attribution

FairHire AI is developed for explainable, responsible, and bias-aware talent acquisition. All candidate profiles generated for testing are strictly synthetic.
