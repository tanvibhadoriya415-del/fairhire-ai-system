
import { useCallback, useEffect, useState } from "react";
import "./JobsPanel.css";

const API = "/api";

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }

  return data;
}

function getExplanation(item) {
  const result = item?.result || {};
  const matchingResult = result.matching_result || {};
  const details = matchingResult.matching_results || {};
  const semantic = result.semantic_result || {};

  return {
    details,
    semantic,
    warnings: Array.isArray(matchingResult.warnings)
      ? matchingResult.warnings
      : [],
    explanation:
      details.explanation ||
      "The system compares extracted resume skills with the skills identified in the job description.",
  };
}

function SkillList({ title, skills, emptyMessage }) {
  const list = Array.isArray(skills) ? skills : [];

  return (
    <div className="jobs-explanation-group">
      <h5>{title}</h5>
      {list.length ? (
        <ul>
          {list.map((skill, index) => (
            <li key={`${skill}-${index}`}>{skill}</li>
          ))}
        </ul>
      ) : (
        <p className="jobs-muted">{emptyMessage || "None listed."}</p>
      )}
    </div>
  );
}

export default function JobsPanel() {
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const selectedJob = jobs.find(
    (job) => String(job.id) === String(jobId)
  );

  const loadJobs = useCallback(async (preferredId = "") => {
    try {
      const data = await request(`${API}/jobs`);
      const list = Array.isArray(data.jobs) ? data.jobs : [];

      setJobs(list);

      setJobId((current) => {
        const wanted = preferredId || current;

        if (list.some((job) => String(job.id) === String(wanted))) {
          return String(wanted);
        }

        return list.length ? String(list[0].id) : "";
      });

      setError("");
    } catch (err) {
      setError(`Could not load jobs: ${err.message}`);
    }
  }, []);

  const loadResults = useCallback(async (id) => {
    if (!id) {
      setResults([]);
      return;
    }

    try {
      const data = await request(`${API}/jobs/${id}/screenings`);
      setResults(Array.isArray(data.screenings) ? data.screenings : []);
    } catch (err) {
      setError(`Could not load saved results: ${err.message}`);
    }
  }, []);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  useEffect(() => {
    loadResults(jobId);
  }, [jobId, loadResults]);

  async function createJob(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);

    try {
      const data = await request(`${API}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
        }),
      });

      setTitle("");
      setDescription("");
      setMessage("Job opening saved successfully.");

      await loadJobs(data.job?.id ? String(data.job.id) : "");
    } catch (err) {
      setError(`Could not create job: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function screenBatch(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!jobId) {
      setError("Create or select a job first.");
      return;
    }

    if (!files.length) {
      setError("Select at least one PDF or DOCX resume.");
      return;
    }

    const form = new FormData();
    files.forEach((file) => form.append("files", file));

    setBusy(true);

    try {
      const data = await request(`${API}/jobs/${jobId}/screen`, {
        method: "POST",
        body: form,
      });

      setMessage(
        `Screening complete: ${data.processed || 0} processed, ${
          data.failed_count || 0
        } failed.`
      );

      setFiles([]);

      const input = document.getElementById("jobs-resume-files");
      if (input) input.value = "";

      await loadResults(jobId);
    } catch (err) {
      setError(`Screening failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  const ranked = [...results].sort((a, b) => {
    const scoreA = a.skill_score == null ? -1 : Number(a.skill_score);
    const scoreB = b.skill_score == null ? -1 : Number(b.skill_score);
    return scoreB - scoreA;
  });

  return (
    <div className="jobs-page">
      <div className="jobs-page-intro">
        <div>
          <div className="jobs-eyebrow">RECRUITMENT WORKSPACE</div>
          <h2>Jobs &amp; Batch Screening</h2>
          <p>
            Create job openings, screen multiple resumes and inspect the
            reasons behind each result.
          </p>
        </div>

        <button
          type="button"
          className="jobs-secondary-button"
          onClick={() => {
            loadJobs(jobId);
            loadResults(jobId);
          }}
          disabled={busy}
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="jobs-alert jobs-alert-error" role="alert">
          {error}
        </div>
      )}

      {message && (
        <div className="jobs-alert jobs-alert-success" role="status">
          {message}
        </div>
      )}

      <div className="jobs-main-grid">
        <section className="jobs-card">
          <h3>01. Create a job opening</h3>

          <form className="jobs-form" onSubmit={createJob}>
            <label htmlFor="jobs-title">Job title</label>
            <input
              id="jobs-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Junior Software Developer"
              required
            />

            <label htmlFor="jobs-description">Job description</label>
            <textarea
              id="jobs-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder={
                "Required Skills:\nPython, SQL, Git\n\nPreferred Skills:\nMachine Learning, Docker"
              }
              rows={8}
              required
            />

            <button
              type="submit"
              className="jobs-primary-button"
              disabled={busy}
            >
              {busy ? "Please wait..." : "Create and save job"}
            </button>
          </form>
        </section>

        <section className="jobs-card">
          <h3>02. Upload a resume batch</h3>

          {jobs.length === 0 ? (
            <p className="jobs-muted">Create a job opening first.</p>
          ) : (
            <form className="jobs-form" onSubmit={screenBatch}>
              <label htmlFor="jobs-select">Select job</label>

              <select
                id="jobs-select"
                value={jobId}
                onChange={(event) => setJobId(event.target.value)}
              >
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title} (ID: {job.id})
                  </option>
                ))}
              </select>

              {selectedJob && (
                <details>
                  <summary>View job description</summary>
                  <p className="jobs-description">
                    {selectedJob.description}
                  </p>
                </details>
              )}

              <label htmlFor="jobs-resume-files">
                Resume files (PDF/DOCX)
              </label>

              <input
                id="jobs-resume-files"
                type="file"
                accept=".pdf,.docx"
                multiple
                onChange={(event) =>
                  setFiles(Array.from(event.target.files || []))
                }
              />

              <p className="jobs-muted">
                {files.length} file(s) selected. Maximum 10 MB per resume.
              </p>

              <button
                type="submit"
                className="jobs-primary-button"
                disabled={busy || !files.length}
              >
                {busy ? "Screening..." : "Screen selected resumes"}
              </button>
            </form>
          )}
        </section>
      </div>

      <section className="jobs-card">
        <h3>03. Saved screening results</h3>

        {!ranked.length ? (
          <p className="jobs-muted">
            No saved screenings for this job yet. Upload resumes above.
          </p>
        ) : (
          <div className="jobs-table-wrap">
            <table className="jobs-table">
              <thead>
                <tr>
                  <th>Rank*</th>
                  <th>Resume</th>
                  <th>Skill overlap</th>
                  <th>Semantic similarity</th>
                  <th>Record ID</th>
                  <th>Explanation</th>
                </tr>
              </thead>

              <tbody>
                {ranked.map((item, index) => {
                  const {
                    details,
                    semantic,
                    warnings,
                    explanation,
                  } = getExplanation(item);

                  const recordId =
                    item.screening_id ?? item.id ?? item.candidate_id;

                  const matchedRequired =
                    details.matched_required_skills || [];
                  const missingRequired =
                    details.missing_required_skills || [];
                  const matchedPreferred =
                    details.matched_preferred_skills || [];
                  const missingPreferred =
                    details.missing_preferred_skills || [];

                  const semanticExplanation =
                    semantic.explanation ||
                    "Semantic similarity compares the meaning of resume text with the job description. It is separate from the skill-overlap score.";

                  return (
                    <tr
                      key={
                        recordId ??
                        `${item.filename || "resume"}-${index}`
                      }
                    >
                      <td>{index + 1}</td>

                      <td>{item.filename || item.name || "Candidate"}</td>

                      <td>
                        {item.skill_score == null
                          ? "N/A"
                          : `${Number(item.skill_score).toFixed(2)}%`}
                      </td>

                      <td>
                        {item.semantic_score == null
                          ? "N/A"
                          : `${Number(item.semantic_score).toFixed(2)}%`}
                      </td>

                      <td>{recordId ?? "—"}</td>

                      <td>
                        <details className="jobs-result-details">
                          <summary>View explanation</summary>

                          <div className="jobs-explanation">
                            <h4>How this result was calculated</h4>

                            <p>{explanation}</p>

                            <div className="jobs-explanation-metrics">
                              <div>
                                <span>Skill-overlap score</span>
                                <strong>
                                  {item.skill_score == null
                                    ? "N/A"
                                    : `${Number(item.skill_score).toFixed(
                                        2
                                      )}%`}
                                </strong>
                              </div>

                              <div>
                                <span>Semantic similarity</span>
                                <strong>
                                  {item.semantic_score == null
                                    ? "N/A"
                                    : `${Number(
                                        item.semantic_score
                                      ).toFixed(2)}%`}
                                </strong>
                              </div>
                            </div>

                            <h4>Required skills</h4>

                            <SkillList
                              title="Matched"
                              skills={matchedRequired}
                              emptyMessage="No matched required skills recorded."
                            />

                            <SkillList
                              title="Missing"
                              skills={missingRequired}
                              emptyMessage="No missing required skills recorded."
                            />

                            <h4>Preferred skills</h4>

                            <SkillList
                              title="Matched"
                              skills={matchedPreferred}
                              emptyMessage="No matched preferred skills recorded."
                            />

                            <SkillList
                              title="Missing"
                              skills={missingPreferred}
                              emptyMessage="No missing preferred skills recorded."
                            />

                            <h4>Scoring method</h4>

                            <p>
                              {details.scoring_method ||
                                "Weighted skill overlap"}
                            </p>

                            <p>
                              Required-skill weight:{" "}
                              {details.weights?.required ?? 2}
                              {" · "}
                              Preferred-skill weight:{" "}
                              {details.weights?.preferred ?? 1}
                            </p>

                            <p>
                              The score reflects the system's identified skill
                              overlap. It does not establish overall
                              qualification or predict hiring success.
                            </p>

                            <h4>Semantic comparison</h4>

                            <p>{semanticExplanation}</p>

                            {semantic.model && (
                              <p>
                                <strong>Model:</strong> {semantic.model}
                              </p>
                            )}

                            {warnings.length > 0 && (
                              <>
                                <h4>Screening warnings</h4>
                                <ul>
                                  {warnings.map((warning, warningIndex) => (
                                    <li key={warningIndex}>{warning}</li>
                                  ))}
                                </ul>
                              </>
                            )}

                            <p className="jobs-explanation-notice">
                              Human review is required. Do not use these
                              scores as the sole basis for hiring decisions.
                            </p>
                          </div>
                        </details>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <p className="jobs-footnote">
          *Sorted by skill-overlap score where available. Skill overlap and
          semantic similarity measure different things; neither is a hiring
          probability. Human review remains necessary.
        </p>
      </section>
    </div>
  );
}
