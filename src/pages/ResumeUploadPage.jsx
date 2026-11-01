import React, { useState, useRef } from "react";
import {
  IconUpload,
  IconFileText,
  IconBriefcase,
  IconCheck,
  IconAlertTriangle,
  IconX,
  IconUsers,
  IconEye,
} from "../components/Icons";

export default function ResumeUploadPage({
  jobs,
  selectedJobId,
  onSelectJob,
  onNavigate,
  onSelectCandidate,
}) {
  const [selectedJob, setSelectedJob] = useState(
    jobs.find((j) => String(j.id) === String(selectedJobId)) || jobs[0] || null
  );
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isScreening, setIsScreening] = useState(false);
  const [screeningResults, setScreeningResults] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const fileInputRef = useRef(null);

  const handleJobChange = (e) => {
    const id = e.target.value;
    const found = jobs.find((j) => String(j.id) === String(id));
    setSelectedJob(found || null);
    if (onSelectJob) onSelectJob(id);
    setScreeningResults(null);
  };

  const handleFilesAdded = (incomingFiles) => {
    setErrorMessage("");
    const allowed = [".pdf", ".docx", ".txt"];
    const validFiles = [];
    const rejected = [];

    Array.from(incomingFiles).forEach((f) => {
      const ext = "." + f.name.split(".").pop().toLowerCase();
      if (!allowed.includes(ext)) {
        rejected.push(`${f.name} (unsupported format)`);
      } else if (f.size > 10 * 1024 * 1024) {
        rejected.push(`${f.name} (exceeds 10MB limit)`);
      } else {
        // Prevent duplicate files in the upload list
        if (!files.some((existing) => existing.name === f.name && existing.size === f.size)) {
          validFiles.push(f);
        }
      }
    });

    if (rejected.length > 0) {
      setErrorMessage(`Some files were skipped: ${rejected.join(", ")}`);
    }

    setFiles((prev) => [...prev, ...validFiles]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearQueue = () => {
    setFiles([]);
    setScreeningResults(null);
    setErrorMessage("");
  };

  const handleStartScreening = async () => {
    if (!selectedJob) {
      setErrorMessage("Please select a job opening first.");
      return;
    }
    if (files.length === 0) {
      setErrorMessage("Please add at least one resume file (.pdf, .docx, or .txt).");
      return;
    }

    setIsScreening(true);
    setErrorMessage("");

    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));

      const res = await fetch(`/api/jobs/${selectedJob.id}/screen`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Screening failed.");
      }

      setScreeningResults(data);
    } catch (err) {
      setErrorMessage(err.message || "Failed to process resumes.");
    } finally {
      setIsScreening(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="page-content">
      {/* Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">BATCH PROCESSING & MATCHING ENGINE</div>
          <h2>Resume Upload & Batch Screening</h2>
          <p className="muted">
            Upload candidate resumes in PDF, DOCX, or TXT format and evaluate them
            against job criteria.
          </p>
        </div>
      </div>

      {/* Target Job Selection Card */}
      <div className="surface-card mb-4">
        <div className="card-header">
          <div className="job-selector-header">
            <IconBriefcase size={20} className="text-indigo" />
            <h3>1. Target Job Opening</h3>
          </div>
          <div className="job-select-wrapper">
            <select
              value={selectedJob?.id || ""}
              onChange={handleJobChange}
              className="job-dropdown-large"
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} ({job.department}) — {job.total_applications || 0} applicants
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedJob && (
          <div className="job-criteria-preview">
            <div className="criteria-row">
              <span className="criteria-label">Required Skills (Weight 2):</span>
              <div className="chips-row">
                {(selectedJob.required_skills || []).map((sk) => (
                  <span key={sk} className="chip-tag matched">
                    {sk}
                  </span>
                ))}
                {(selectedJob.required_skills || []).length === 0 && (
                  <span className="text-muted small">None explicitly specified</span>
                )}
              </div>
            </div>
            <div className="criteria-row mt-2">
              <span className="criteria-label">Preferred Skills (Weight 1):</span>
              <div className="chips-row">
                {(selectedJob.preferred_skills || []).map((sk) => (
                  <span key={sk} className="chip-tag standard">
                    {sk}
                  </span>
                ))}
                {(selectedJob.preferred_skills || []).length === 0 && (
                  <span className="text-muted small">None specified</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Drag & Drop Upload Zone */}
      <div className="surface-card mb-4">
        <div className="card-header">
          <h3>2. Upload Candidate Resumes</h3>
          <span className="badge-pill neutral">PDF, DOCX, TXT • Max 10MB</span>
        </div>

        <div
          className={`dropzone-area ${isDragging ? "dragging" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            multiple
            accept=".pdf,.docx,.txt"
            style={{ display: "none" }}
            onChange={(e) => handleFilesAdded(e.target.files)}
          />
          <div className="dropzone-icon">
            <IconUpload size={36} className="text-indigo" />
          </div>
          <h4>Drag & Drop resumes here, or click to browse</h4>
          <p className="muted small">
            Batch processing accepts multiple files simultaneously. Text will be
            extracted, parsed, and evaluated against the selected job.
          </p>
        </div>

        {/* Error notification */}
        {errorMessage && (
          <div className="alert-box error mt-3">
            <IconAlertTriangle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* File Queue List */}
        {files.length > 0 && (
          <div className="upload-queue mt-4">
            <div className="queue-header">
              <h4>Selected Resumes ({files.length})</h4>
              <button className="text-button small" onClick={clearQueue}>
                Clear All
              </button>
            </div>
            <div className="queue-list">
              {files.map((file, idx) => (
                <div key={`${file.name}-${idx}`} className="queue-item">
                  <div className="queue-item-info">
                    <IconFileText size={18} className="text-muted" />
                    <div>
                      <strong>{file.name}</strong>
                      <small className="muted">{formatFileSize(file.size)}</small>
                    </div>
                  </div>
                  <button
                    className="icon-remove-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(idx);
                    }}
                    title="Remove file"
                  >
                    <IconX size={16} />
                  </button>
                </div>
              ))}
            </div>

            <div className="screening-cta-bar mt-4">
              <button
                className="primary-button cta-large"
                onClick={handleStartScreening}
                disabled={isScreening}
              >
                <IconUpload size={18} />
                {isScreening
                  ? `Screening ${files.length} resume(s)...`
                  : `Start Screening Batch (${files.length} Resumes)`}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Screening Results Panel */}
      {screeningResults && (
        <div className="surface-card results-card mb-4">
          <div className="card-header">
            <div>
              <div className="badge-pill positive mb-1">Screening Complete</div>
              <h3>Batch Screening Results</h3>
              <p className="muted small">
                Successfully processed {screeningResults.processed_count} of{" "}
                {files.length} resumes for <strong>{screeningResults.job_title}</strong>.
              </p>
            </div>
            <button
              className="primary-button"
              onClick={() => onNavigate("candidates")}
            >
              <IconUsers size={16} /> View in Candidate Explorer →
            </button>
          </div>

          <div className="results-table-wrap mt-3">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate Name</th>
                  <th>Original File</th>
                  <th>Match Score</th>
                  <th>Required Coverage</th>
                  <th>Matched Skills</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {screeningResults.results.map((r) => (
                  <tr key={r.application_id}>
                    <td className="font-semibold text-light">{r.candidate_name}</td>
                    <td className="text-muted small">{r.filename}</td>
                    <td>
                      <span
                        className={`score-pill ${
                          (r.overall_score || 0) >= 70
                            ? "high"
                            : (r.overall_score || 0) >= 45
                            ? "medium"
                            : "low"
                        }`}
                      >
                        {r.overall_score != null ? `${r.overall_score.toFixed(1)}%` : "N/A"}
                      </span>
                    </td>
                    <td>
                      <span className="coverage-text">
                        {r.required_skill_coverage != null
                          ? `${r.required_skill_coverage.toFixed(0)}%`
                          : "N/A"}
                      </span>
                    </td>
                    <td>
                      <div className="skill-chips-mini">
                        {(r.matched_required_skills || []).map((sk) => (
                          <span key={sk} className="chip-tag matched">
                            {sk}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <button
                        className="action-btn-sm"
                        onClick={() => onSelectCandidate(r.application_id)}
                      >
                        <IconEye size={14} /> Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {screeningResults.errors?.length > 0 && (
            <div className="errors-breakdown mt-3">
              <span className="text-amber small font-semibold">
                Screening notices ({screeningResults.errors.length}):
              </span>
              <ul className="small muted">
                {screeningResults.errors.map((err, i) => (
                  <li key={i}>
                    <strong>{err.filename}:</strong> {err.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
