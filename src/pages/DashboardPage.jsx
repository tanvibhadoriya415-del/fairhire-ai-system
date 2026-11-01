import React from "react";
import {
  IconBriefcase,
  IconUsers,
  IconUpload,
  IconCheck,
  IconClock,
  IconAlertTriangle,
  IconSparkles,
  IconEye,
  IconScale,
} from "../components/Icons";

export default function DashboardPage({
  stats,
  loading,
  onNavigate,
  onSelectCandidate,
  onSeedDemo,
  seeding,
}) {
  const recentScreenings = stats?.recent_screenings || [];
  const recentJobs = stats?.recent_jobs || [];

  return (
    <div className="page-content">
      {/* Top Banner / Welcome */}
      <div className="dashboard-welcome-banner">
        <div className="banner-content">
          <div className="eyebrow">RECRUITMENT INTELLIGENCE & GOVERNANCE</div>
          <h2>HR Screening Overview</h2>
          <p className="banner-desc">
            FairHire AI provides explainable, job-specific candidate screening
            with evidence transparency and responsible-AI guardrails.
          </p>
          <div className="banner-actions">
            <button className="primary-button" onClick={() => onNavigate("upload")}>
              <IconUpload size={16} /> Screen Resumes Batch
            </button>
            <button className="secondary-button" onClick={() => onNavigate("jobs")}>
              <IconBriefcase size={16} /> Manage Jobs
            </button>
            <button
              className="accent-button"
              onClick={onSeedDemo}
              disabled={seeding}
              title="Loads realistic sample jobs and synthetic applicants for demonstration"
            >
              <IconSparkles size={16} /> {seeding ? "Seeding..." : "Load Sample HR Data"}
            </button>
          </div>
        </div>
      </div>

      {/* Primary KPI Metric Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon-wrap blue">
            <IconBriefcase size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Active Job Openings</span>
            <strong className="metric-value">
              {loading ? "..." : stats?.active_jobs ?? 0}
            </strong>
            <small className="metric-sub">
              {stats?.total_jobs ?? 0} total openings created
            </small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap indigo">
            <IconUsers size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Total Applications</span>
            <strong className="metric-value">
              {loading ? "..." : stats?.total_applications ?? 0}
            </strong>
            <small className="metric-sub">
              {stats?.processed_resumes ?? 0} successfully screened
            </small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap amber">
            <IconClock size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Awaiting HR Review</span>
            <strong className="metric-value">
              {loading ? "..." : stats?.awaiting_review ?? 0}
            </strong>
            <small className="metric-sub">Applied or Under Review</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap green">
            <IconCheck size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Shortlisted Candidates</span>
            <strong className="metric-value">
              {loading ? "..." : stats?.shortlisted_candidates ?? 0}
            </strong>
            <small className="metric-sub">
              {stats?.interviews_scheduled ?? 0} interview(s) scheduled
            </small>
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="dashboard-columns">
        {/* Left Column: Recent Screening Activity */}
        <div className="surface-card col-wide">
          <div className="card-header">
            <div>
              <h3>Recent Candidate Screenings</h3>
              <p className="muted small">Live applications evaluated against job criteria</p>
            </div>
            <button
              className="text-link-button"
              onClick={() => onNavigate("candidates")}
            >
              Open Candidate Explorer →
            </button>
          </div>

          {recentScreenings.length > 0 ? (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Role Applied</th>
                    <th>Match Score</th>
                    <th>HR Status</th>
                    <th>Date</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recentScreenings.map((sc) => (
                    <tr key={sc.application_id}>
                      <td className="font-semibold text-light">
                        <div className="cand-cell">
                          <span className="avatar-mini">
                            {(sc.candidate_name || "C").charAt(0).toUpperCase()}
                          </span>
                          {sc.candidate_name}
                        </div>
                      </td>
                      <td className="text-muted">{sc.job_title}</td>
                      <td>
                        <span
                          className={`score-pill ${
                            (sc.overall_score || 0) >= 70
                              ? "high"
                              : (sc.overall_score || 0) >= 45
                              ? "medium"
                              : "low"
                          }`}
                        >
                          {sc.overall_score != null
                            ? `${sc.overall_score.toFixed(1)}%`
                            : "N/A"}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`status-badge badge-${
                            sc.hr_status === "shortlisted"
                              ? "shortlisted"
                              : sc.hr_status === "under_review"
                              ? "review"
                              : "applied"
                          }`}
                        >
                          {sc.hr_status ? sc.hr_status.replace("_", " ") : "applied"}
                        </span>
                      </td>
                      <td className="text-muted small">{sc.created_at?.slice(0, 10)}</td>
                      <td>
                        <button
                          className="action-btn-sm"
                          onClick={() => onSelectCandidate(sc.application_id)}
                          title="Open candidate profile and evidence"
                        >
                          <IconEye size={14} /> View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <IconUsers size={32} className="text-muted" />
              <h4>No Screened Candidates Yet</h4>
              <p className="muted">
                Create a job opening and upload candidate resumes, or click "Load Sample HR Data" above.
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Active Jobs & Fairness Summary */}
        <div className="surface-card col-narrow">
          <div className="card-header">
            <div>
              <h3>Recent Job Openings</h3>
              <p className="muted small">Pipeline counts per role</p>
            </div>
            <button className="text-link-button" onClick={() => onNavigate("jobs")}>
              All Jobs →
            </button>
          </div>

          <div className="jobs-list-mini">
            {recentJobs.length > 0 ? (
              recentJobs.map((job) => (
                <div key={job.id} className="job-mini-item">
                  <div className="job-mini-info">
                    <strong>{job.title}</strong>
                    <small>
                      {job.department} •{" "}
                      <span className={`status-dot ${job.status}`} /> {job.status}
                    </small>
                  </div>
                  <div className="job-mini-metric">
                    <span>{job.candidate_count || 0}</span>
                    <small>Applicants</small>
                  </div>
                </div>
              ))
            ) : (
              <p className="empty-muted">No job openings created yet.</p>
            )}
          </div>

          <div className="fairness-card-promo mt-4">
            <div className="promo-top">
              <IconScale size={20} className="text-indigo" />
              <strong>Responsible-AI Safeguards Active</strong>
            </div>
            <p className="small muted">
              All demographic attributes (gender, race, age, religion) are excluded
              from match formulas. All hiring stage transitions are human-supervised.
            </p>
            <button
              className="text-link-button small"
              onClick={() => onNavigate("fairness")}
            >
              Inspect Fairness & Score Audit →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
