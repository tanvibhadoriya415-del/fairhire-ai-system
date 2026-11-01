import React, { useState } from "react";
import {
  IconX,
  IconCheck,
  IconAlertTriangle,
  IconClock,
  IconShield,
  IconFileText,
  IconBriefcase,
  IconScale,
} from "./Icons";

export default function CandidateDetailDrawer({
  application,
  onClose,
  onStatusChange,
  onNotesChange,
}) {
  if (!application) return null;

  const [activeTab, setActiveTab] = useState("analysis");
  const [currentStatus, setCurrentStatus] = useState(application.hr_status || "applied");
  const [statusNote, setStatusNote] = useState("");
  const [notes, setNotes] = useState(application.notes || "");
  const [isSavingStatus, setIsSavingStatus] = useState(false);
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const [expandedSkill, setExpandedSkill] = useState(null);

  const matchedReq = application.matched_required_skills || [];
  const missingReq = application.missing_required_skills || [];
  const matchedPref = application.matched_preferred_skills || [];
  const missingPref = application.missing_preferred_skills || [];
  const evidence = application.evidence || {};
  const history = application.status_history || [];

  const handleStatusSubmit = async (newStatus) => {
    setIsSavingStatus(true);
    try {
      await onStatusChange(application.application_id, newStatus, statusNote);
      setCurrentStatus(newStatus);
      setStatusNote("");
    } catch (err) {
      alert("Failed to update status: " + err.message);
    } finally {
      setIsSavingStatus(false);
    }
  };

  const handleNotesSubmit = async () => {
    setIsSavingNotes(true);
    try {
      await onNotesChange(application.application_id, notes);
      alert("HR notes saved successfully.");
    } catch (err) {
      alert("Failed to save notes: " + err.message);
    } finally {
      setIsSavingNotes(false);
    }
  };

  const getStatusBadgeClass = (status) => {
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
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-container" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-title-area">
            <div className="drawer-avatar">
              {(application.candidate_name || "C").charAt(0).toUpperCase()}
            </div>
            <div>
              <h3>{application.candidate_name}</h3>
              <p className="drawer-subtitle">
                {application.candidate_headline || "Candidate Profile"} • Applied for{" "}
                <span className="text-highlight">{application.job_title}</span>
              </p>
              <div className="drawer-contact-chips">
                {application.candidate_email && (
                  <span className="contact-chip">✉ {application.candidate_email}</span>
                )}
                {application.candidate_phone && (
                  <span className="contact-chip">☎ {application.candidate_phone}</span>
                )}
                <span className={`status-badge ${getStatusBadgeClass(currentStatus)}`}>
                  {currentStatus.replace("_", " ").toUpperCase()}
                </span>
              </div>
            </div>
          </div>
          <button className="icon-close-btn" onClick={onClose} title="Close Profile">
            <IconX size={20} />
          </button>
        </div>

        {/* Score Overview Bar */}
        <div className="drawer-score-strip">
          <div className="score-strip-item primary">
            <span className="label">Overall Match Score</span>
            <div className="score-val">
              {application.overall_score != null ? `${application.overall_score.toFixed(1)}%` : "N/A"}
            </div>
            <small>Weighted Evidence Alignment</small>
          </div>
          <div className="score-strip-item">
            <span className="label">Required Skill Coverage</span>
            <div className="score-val">
              {application.required_skill_coverage != null
                ? `${application.required_skill_coverage.toFixed(0)}%`
                : "N/A"}
            </div>
            <small>
              {matchedReq.length} of {matchedReq.length + missingReq.length} required
            </small>
          </div>
          <div className="score-strip-item">
            <span className="label">Semantic Relevance</span>
            <div className="score-val">
              {application.semantic_score != null
                ? `${application.semantic_score.toFixed(1)}%`
                : "Calculated"}
            </div>
            <small>Textual Context Similarity</small>
          </div>
          <div className="score-strip-item">
            <span className="label">Experience Detected</span>
            <div className="score-val">
              {application.experience_years_detected != null
                ? `${application.experience_years_detected} yrs`
                : "Unknown"}
            </div>
            <small>Stated in resume</small>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="drawer-tabs">
          <button
            className={`drawer-tab ${activeTab === "analysis" ? "active" : ""}`}
            onClick={() => setActiveTab("analysis")}
          >
            <IconScale size={16} /> Job Match & Evidence
          </button>
          <button
            className={`drawer-tab ${activeTab === "resume" ? "active" : ""}`}
            onClick={() => setActiveTab("resume")}
          >
            <IconFileText size={16} /> Extracted Resume
          </button>
          <button
            className={`drawer-tab ${activeTab === "actions" ? "active" : ""}`}
            onClick={() => setActiveTab("actions")}
          >
            <IconBriefcase size={16} /> HR Actions & Notes
          </button>
          <button
            className={`drawer-tab ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            <IconClock size={16} /> Status History ({history.length})
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="drawer-body">
          {activeTab === "analysis" && (
            <div className="tab-pane">
              {/* Scoring Notice */}
              <div className="alert-notice">
                <IconShield size={18} className="text-indigo" />
                <div>
                  <strong>Explainable Evidence Matching</strong>
                  <p>
                    Required skills carry weight 2; preferred skills carry weight 1.
                    Scores quantify textual alignment with stated job criteria and do
                    not replace human judgment.
                  </p>
                </div>
              </div>

              {/* Matched Required Skills */}
              <div className="analysis-group">
                <div className="group-header">
                  <h4>Matched Required Skills ({matchedReq.length})</h4>
                  <span className="badge-pill positive">Weight 2</span>
                </div>
                {matchedReq.length > 0 ? (
                  <div className="skill-evidence-list">
                    {matchedReq.map((skill) => (
                      <div key={skill} className="evidence-card">
                        <div
                          className="evidence-card-header"
                          onClick={() =>
                            setExpandedSkill(expandedSkill === skill ? null : skill)
                          }
                        >
                          <span className="skill-name">
                            <IconCheck size={16} className="text-green" /> {skill}
                          </span>
                          <span className="evidence-count">
                            {(evidence[skill] || []).length} resume excerpts ▾
                          </span>
                        </div>
                        {(expandedSkill === skill || (evidence[skill] || []).length === 1) && (
                          <div className="evidence-quotes">
                            {(evidence[skill] || ["Identified in skills section."]).map(
                              (quote, idx) => (
                                <blockquote key={idx}>“{quote}”</blockquote>
                              )
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="empty-muted">No required skills were detected in this resume.</p>
                )}
              </div>

              {/* Missing Required Skills */}
              <div className="analysis-group">
                <div className="group-header">
                  <h4>Required Skills Not Detected ({missingReq.length})</h4>
                  <span className="badge-pill warning">Review Needed</span>
                </div>
                {missingReq.length > 0 ? (
                  <div className="missing-chips">
                    {missingReq.map((skill) => (
                      <span key={skill} className="missing-chip">
                        <IconAlertTriangle size={14} /> {skill}
                        <small>(Not detected)</small>
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-green small">✓ All stated required skills were detected!</p>
                )}
              </div>

              {/* Preferred Skills */}
              <div className="analysis-group">
                <div className="group-header">
                  <h4>Preferred Skills ({matchedPref.length} of {matchedPref.length + missingPref.length})</h4>
                  <span className="badge-pill neutral">Weight 1</span>
                </div>
                <div className="chips-row">
                  {matchedPref.map((s) => (
                    <span key={s} className="chip-tag matched">
                      ✓ {s}
                    </span>
                  ))}
                  {missingPref.map((s) => (
                    <span key={s} className="chip-tag missing">
                      - {s}
                    </span>
                  ))}
                </div>
              </div>

              {/* Score Calculation Breakdown */}
              <div className="score-breakdown-card">
                <h5>Scoring Formula Breakdown</h5>
                <div className="breakdown-grid">
                  <div>
                    <span>Required Points Earned:</span>
                    <strong>{matchedReq.length * 2} pts</strong>
                  </div>
                  <div>
                    <span>Preferred Points Earned:</span>
                    <strong>{matchedPref.length * 1} pts</strong>
                  </div>
                  <div>
                    <span>Total Points Earned:</span>
                    <strong>{matchedReq.length * 2 + matchedPref.length * 1} pts</strong>
                  </div>
                  <div>
                    <span>Total Points Possible:</span>
                    <strong>
                      {(matchedReq.length + missingReq.length) * 2 +
                        (matchedPref.length + missingPref.length) * 1}{" "}
                      pts
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "resume" && (
            <div className="tab-pane">
              {application.candidate_summary && (
                <div className="resume-section">
                  <h5>Professional Summary</h5>
                  <p>{application.candidate_summary}</p>
                </div>
              )}

              <div className="resume-section">
                <h5>Extracted Skills</h5>
                <div className="chips-row">
                  {(application.candidate_skills || []).map((sk) => (
                    <span key={sk} className="chip-tag standard">
                      {sk}
                    </span>
                  ))}
                </div>
              </div>

              {application.experience_text && (
                <div className="resume-section">
                  <h5>Work Experience</h5>
                  <div className="raw-text-block">{application.experience_text}</div>
                </div>
              )}

              {application.education_text && (
                <div className="resume-section">
                  <h5>Education</h5>
                  <div className="raw-text-block">{application.education_text}</div>
                </div>
              )}

              {application.projects_text && (
                <div className="resume-section">
                  <h5>Projects</h5>
                  <div className="raw-text-block">{application.projects_text}</div>
                </div>
              )}

              <div className="resume-section">
                <h5>Original Resume Text (Preview)</h5>
                <pre className="resume-raw-preview">{application.raw_text || "No preview available."}</pre>
              </div>
            </div>
          )}

          {activeTab === "actions" && (
            <div className="tab-pane">
              <div className="action-card">
                <h4>Update Recruitment Stage</h4>
                <p className="muted small">
                  Record hiring decisions. Decisions are strictly under human HR control
                  and never automated by match score thresholds.
                </p>

                <div className="stage-buttons-grid">
                  {[
                    { id: "applied", label: "Applied", cls: "btn-applied" },
                    { id: "under_review", label: "Under Review", cls: "btn-review" },
                    { id: "shortlisted", label: "Shortlist", cls: "btn-shortlist" },
                    { id: "interview_scheduled", label: "Interview", cls: "btn-interview" },
                    { id: "offer_pending", label: "Offer Pending", cls: "btn-offer" },
                    { id: "rejected", label: "Reject", cls: "btn-reject" },
                  ].map((btn) => (
                    <button
                      key={btn.id}
                      className={`stage-btn ${btn.cls} ${currentStatus === btn.id ? "active" : ""}`}
                      onClick={() => handleStatusSubmit(btn.id)}
                      disabled={isSavingStatus}
                    >
                      {currentStatus === btn.id && "✓ "}
                      {btn.label}
                    </button>
                  ))}
                </div>

                <div className="stage-note-input">
                  <label>Status Change Note (Optional audit reason):</label>
                  <input
                    type="text"
                    value={statusNote}
                    onChange={(e) => setStatusNote(e.target.value)}
                    placeholder="e.g. Cleared technical interview round 1"
                  />
                </div>
              </div>

              <div className="action-card">
                <h4>Internal HR Notes</h4>
                <p className="muted small">
                  Private recruitment notes preserved across sessions.
                </p>
                <textarea
                  rows={4}
                  className="notes-textarea"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Record interview notes, salary expectations, or portfolio observations..."
                />
                <button
                  className="primary-button mt-2"
                  onClick={handleNotesSubmit}
                  disabled={isSavingNotes}
                >
                  {isSavingNotes ? "Saving..." : "Save HR Notes"}
                </button>
              </div>
            </div>
          )}

          {activeTab === "history" && (
            <div className="tab-pane">
              <div className="history-timeline">
                {history.length > 0 ? (
                  history.map((item, idx) => (
                    <div key={idx} className="timeline-item">
                      <div className="timeline-marker" />
                      <div className="timeline-content">
                        <div className="timeline-header">
                          <strong className="status-label">
                            {item.new_status ? item.new_status.replace("_", " ").toUpperCase() : "UPDATED"}
                          </strong>
                          <span className="timeline-date">{item.created_at}</span>
                        </div>
                        {item.previous_status && (
                          <div className="timeline-prev">
                            Previous status: <span>{item.previous_status}</span>
                          </div>
                        )}
                        {item.note && <p className="timeline-note">“{item.note}”</p>}
                        <small className="timeline-actor">By {item.actor || "HR Recruiter"}</small>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="empty-muted">No status transitions recorded yet.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
