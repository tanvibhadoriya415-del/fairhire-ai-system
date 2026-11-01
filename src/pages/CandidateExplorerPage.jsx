import React, { useState, useEffect } from "react";
import {
  IconSearch,
  IconFilter,
  IconDownload,
  IconRefresh,
  IconUsers,
  IconEye,
  IconArrowUpDown,
  IconCheck,
  IconAlertTriangle,
  IconX,
} from "../components/Icons";

export default function CandidateExplorerPage({
  jobs,
  selectedJobId,
  onSelectJob,
  onSelectCandidate,
  onStatusChange,
}) {
  const [currentJobId, setCurrentJobId] = useState(
    selectedJobId || (jobs.length > 0 ? jobs[0].id : "")
  );
  const [candidates, setCandidates] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Filters state
  const [search, setSearch] = useState("");
  const [minScore, setMinScore] = useState("");
  const [maxScore, setMaxScore] = useState("");
  const [hrStatus, setHrStatus] = useState("all");
  const [requiredSkill, setRequiredSkill] = useState("");
  const [matchedSkill, setMatchedSkill] = useState("");
  const [missingSkill, setMissingSkill] = useState("");
  const [minExperience, setMinExperience] = useState("");
  const [sortBy, setSortBy] = useState("score_desc");
  const [showFiltersPanel, setShowFiltersPanel] = useState(false);

  const activeJob = jobs.find((j) => String(j.id) === String(currentJobId)) || null;

  const fetchCandidates = async () => {
    if (!currentJobId) {
      setCandidates([]);
      setTotalCount(0);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();
      if (search.trim()) params.append("search", search.trim());
      if (minScore !== "") params.append("min_score", minScore);
      if (maxScore !== "") params.append("max_score", maxScore);
      if (hrStatus && hrStatus !== "all") params.append("hr_status", hrStatus);
      if (requiredSkill.trim()) params.append("required_skill", requiredSkill.trim());
      if (matchedSkill.trim()) params.append("matched_skill", matchedSkill.trim());
      if (missingSkill.trim()) params.append("missing_skill", missingSkill.trim());
      if (minExperience !== "") params.append("min_experience", minExperience);
      params.append("sort_by", sortBy);
      params.append("limit", "100");

      const res = await fetch(`/api/jobs/${currentJobId}/candidates?${params.toString()}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Could not retrieve candidate records.");
      }

      setCandidates(data.candidates || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      setError(err.message || "Failed to load candidates.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [
    currentJobId,
    search,
    minScore,
    maxScore,
    hrStatus,
    requiredSkill,
    matchedSkill,
    missingSkill,
    minExperience,
    sortBy,
  ]);

  const handleJobSelect = (e) => {
    const id = e.target.value;
    setCurrentJobId(id);
    if (onSelectJob) onSelectJob(id);
  };

  const handleClearFilters = () => {
    setSearch("");
    setMinScore("");
    setMaxScore("");
    setHrStatus("all");
    setRequiredSkill("");
    setMatchedSkill("");
    setMissingSkill("");
    setMinExperience("");
    setSortBy("score_desc");
  };

  const handleExportCsv = () => {
    if (!currentJobId) return;
    window.location.href = `/api/jobs/${currentJobId}/export.csv`;
  };

  const handleInlineStatusChange = async (appId, newStatus) => {
    try {
      await onStatusChange(appId, newStatus, "Status updated from Candidate Explorer table");
      fetchCandidates();
    } catch (err) {
      alert("Status update failed: " + err.message);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "shortlisted":
        return "badge-shortlisted";
      case "interview_scheduled":
        return "badge-interview";
      case "under_review":
        return "badge-review";
      case "rejected":
        return "badge-rejected";
      case "offer_pending":
        return "badge-offer";
      default:
        return "badge-applied";
    }
  };

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">CANDIDATE INTELLIGENCE & EVALUATION</div>
          <h2>Candidate Explorer</h2>
          <p className="muted">
            Search, filter, and sort applicants evaluated against job criteria.
          </p>
        </div>
        <div className="header-actions">
          <button
            className="secondary-button"
            onClick={handleExportCsv}
            disabled={!currentJobId || candidates.length === 0}
            title="Download candidate screening results as CSV"
          >
            <IconDownload size={16} /> Export CSV
          </button>
        </div>
      </div>

      {/* Mandatory Job Opening Selector Bar */}
      <div className="surface-card job-filter-banner mb-4">
        <div className="job-banner-inner">
          <div className="job-banner-select">
            <label className="font-semibold text-light">Select Job Opening:</label>
            <select
              value={currentJobId}
              onChange={handleJobSelect}
              className="job-dropdown-large"
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} ({job.department}) — {job.total_applications || 0} applicants
                </option>
              ))}
            </select>
          </div>

          {activeJob && (
            <div className="job-banner-stats">
              <div className="banner-kpi">
                <span className="label">Total Applicants</span>
                <strong>{totalCount}</strong>
              </div>
              <div className="banner-kpi">
                <span className="label">Average Score</span>
                <strong>
                  {activeJob.average_score != null
                    ? `${activeJob.average_score.toFixed(1)}%`
                    : "N/A"}
                </strong>
              </div>
              <div className="banner-kpi">
                <span className="label">Shortlisted</span>
                <strong>{activeJob.shortlisted_count || 0}</strong>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="surface-card mb-4">
        <div className="filter-toolbar">
          <div className="search-input-wrap">
            <IconSearch size={18} className="text-muted" />
            <input
              type="text"
              placeholder="Search candidate name, email, skills, resume keywords..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button className="clear-search-btn" onClick={() => setSearch("")}>
                <IconX size={14} />
              </button>
            )}
          </div>

          <div className="toolbar-controls">
            <button
              className={`filter-toggle-btn ${showFiltersPanel ? "active" : ""}`}
              onClick={() => setShowFiltersPanel(!showFiltersPanel)}
            >
              <IconFilter size={16} /> Filters
              {(minScore || maxScore || hrStatus !== "all" || matchedSkill || minExperience) && (
                <span className="active-dot" />
              )}
            </button>

            <div className="sort-select-wrap">
              <IconArrowUpDown size={14} className="text-muted" />
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="score_desc">Highest Match Score First</option>
                <option value="score_asc">Lowest Match Score First</option>
                <option value="coverage_desc">Highest Required Coverage First</option>
                <option value="coverage_asc">Lowest Required Coverage First</option>
                <option value="experience_desc">Most Relevant Experience First</option>
                <option value="experience_asc">Least Experience First</option>
                <option value="date_desc">Newest Applications First</option>
                <option value="date_asc">Oldest Applications First</option>
                <option value="name_asc">Candidate Name (A–Z)</option>
                <option value="name_desc">Candidate Name (Z–A)</option>
              </select>
            </div>

            <button
              className="icon-refresh-btn"
              onClick={fetchCandidates}
              title="Refresh list"
            >
              <IconRefresh size={16} />
            </button>
          </div>
        </div>

        {/* Collapsible Advanced Filters Panel */}
        {showFiltersPanel && (
          <div className="advanced-filters-panel mt-3 pt-3 border-t">
            <div className="filters-grid">
              <div className="filter-item">
                <label>Min Score (%):</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={minScore}
                  onChange={(e) => setMinScore(e.target.value)}
                  placeholder="e.g. 60"
                />
              </div>

              <div className="filter-item">
                <label>Max Score (%):</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={maxScore}
                  onChange={(e) => setMaxScore(e.target.value)}
                  placeholder="e.g. 100"
                />
              </div>

              <div className="filter-item">
                <label>Recruitment Stage:</label>
                <select
                  value={hrStatus}
                  onChange={(e) => setHrStatus(e.target.value)}
                >
                  <option value="all">All Stages</option>
                  <option value="applied">Applied</option>
                  <option value="under_review">Under Review</option>
                  <option value="shortlisted">Shortlisted</option>
                  <option value="interview_scheduled">Interview Scheduled</option>
                  <option value="offer_pending">Offer Pending</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              <div className="filter-item">
                <label>Must Have Skill:</label>
                <input
                  type="text"
                  value={matchedSkill}
                  onChange={(e) => setMatchedSkill(e.target.value)}
                  placeholder="e.g. python, sql, react"
                />
              </div>

              <div className="filter-item">
                <label>Missing Skill Filter:</label>
                <input
                  type="text"
                  value={missingSkill}
                  onChange={(e) => setMissingSkill(e.target.value)}
                  placeholder="Filter missing skill..."
                />
              </div>

              <div className="filter-item">
                <label>Min Experience (Yrs):</label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={minExperience}
                  onChange={(e) => setMinExperience(e.target.value)}
                  placeholder="e.g. 1"
                />
              </div>
            </div>

            <div className="filters-footer mt-3">
              <button className="text-button small" onClick={handleClearFilters}>
                Clear All Filters
              </button>
              <span className="muted small">
                Showing {candidates.length} of {totalCount} matching applicants
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Candidates Data Table */}
      <div className="surface-card">
        {loading ? (
          <div className="loading-state">
            <IconRefresh size={32} className="spin text-indigo" />
            <p className="mt-2">Loading candidates for {activeJob?.title}...</p>
          </div>
        ) : candidates.length > 0 ? (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Match Score</th>
                  <th>Required Coverage</th>
                  <th>Matched Required Skills</th>
                  <th>Skills Not Detected</th>
                  <th>Experience</th>
                  <th>HR Stage</th>
                  <th>Applied</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((cand) => (
                  <tr key={cand.application_id}>
                    <td>
                      <div className="cand-cell">
                        <span className="avatar-mini">
                          {(cand.candidate_name || "C").charAt(0).toUpperCase()}
                        </span>
                        <div>
                          <strong>{cand.candidate_name}</strong>
                          {cand.candidate_email && (
                            <small className="muted block">{cand.candidate_email}</small>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span
                        className={`score-pill large ${
                          (cand.overall_score || 0) >= 70
                            ? "high"
                            : (cand.overall_score || 0) >= 45
                            ? "medium"
                            : "low"
                        }`}
                      >
                        {cand.overall_score != null
                          ? `${cand.overall_score.toFixed(1)}%`
                          : "N/A"}
                      </span>
                    </td>
                    <td>
                      <span className="font-semibold text-light">
                        {cand.required_skill_coverage != null
                          ? `${cand.required_skill_coverage.toFixed(0)}%`
                          : "N/A"}
                      </span>
                    </td>
                    <td>
                      <div className="skill-chips-mini">
                        {(cand.matched_required_skills || []).map((sk) => (
                          <span key={sk} className="chip-tag matched">
                            ✓ {sk}
                          </span>
                        ))}
                        {(cand.matched_required_skills || []).length === 0 && (
                          <span className="text-muted small">None</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="skill-chips-mini">
                        {(cand.missing_required_skills || []).map((sk) => (
                          <span key={sk} className="chip-tag missing">
                            - {sk}
                          </span>
                        ))}
                        {(cand.missing_required_skills || []).length === 0 && (
                          <span className="text-green small">✓ All matched</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="text-muted">
                        {cand.experience_years_detected != null
                          ? `${cand.experience_years_detected} yrs`
                          : "Unknown"}
                      </span>
                    </td>
                    <td>
                      <select
                        className={`status-select ${getStatusBadge(cand.hr_status)}`}
                        value={cand.hr_status || "applied"}
                        onChange={(e) =>
                          handleInlineStatusChange(cand.application_id, e.target.value)
                        }
                      >
                        <option value="applied">Applied</option>
                        <option value="under_review">Under Review</option>
                        <option value="shortlisted">Shortlisted</option>
                        <option value="interview_scheduled">Interview Scheduled</option>
                        <option value="offer_pending">Offer Pending</option>
                        <option value="rejected">Rejected</option>
                      </select>
                    </td>
                    <td className="text-muted small">
                      {cand.application_date?.slice(0, 10)}
                    </td>
                    <td>
                      <button
                        className="action-btn-sm"
                        onClick={() => onSelectCandidate(cand.application_id)}
                        title="View complete candidate match evidence and profile"
                      >
                        <IconEye size={14} /> Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <IconUsers size={36} className="text-muted" />
            <h4>No Candidates Match Current Criteria</h4>
            <p className="muted">
              {search || minScore || hrStatus !== "all"
                ? "Try clearing filters to see more candidate applications."
                : `No candidates screened for ${activeJob?.title || "this job"} yet.`}
            </p>
            {(search || minScore || hrStatus !== "all") && (
              <button className="secondary-button mt-3" onClick={handleClearFilters}>
                Clear All Filters
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
