import React, { useState } from "react";
import {
  IconPlus,
  IconSearch,
  IconFilter,
  IconBriefcase,
  IconUsers,
  IconUpload,
  IconRefresh,
  IconX,
  IconCheck,
  IconSparkles,
  IconEye,
} from "../components/Icons";

export default function JobManagementPage({
  jobs,
  loading,
  onRefresh,
  onCreateJob,
  onUpdateJob,
  onSelectJobForCandidates,
  onSelectJobForUpload,
  onRescreenJob,
}) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [parsingSkills, setParsingSkills] = useState(false);

  // Form state
  const [formTitle, setFormTitle] = useState("");
  const [formDept, setFormDept] = useState("Engineering");
  const [formDesc, setFormDesc] = useState("");
  const [formResp, setFormResp] = useState("");
  const [formReqSkills, setFormReqSkills] = useState(["python", "sql", "git"]);
  const [formPrefSkills, setFormPrefSkills] = useState(["docker", "rest api"]);
  const [formReqInput, setFormReqInput] = useState("");
  const [formPrefInput, setFormPrefInput] = useState("");
  const [formMinExp, setFormMinExp] = useState(0);
  const [formEdu, setFormEdu] = useState("");
  const [formType, setFormType] = useState("Full-time");
  const [formLocation, setFormLocation] = useState("Remote / Hybrid");
  const [formStatus, setFormStatus] = useState("active");

  const openCreateModal = () => {
    setEditingJob(null);
    setFormTitle("");
    setFormDept("Engineering");
    setFormDesc("");
    setFormResp("");
    setFormReqSkills(["python", "sql", "git"]);
    setFormPrefSkills(["docker", "rest api"]);
    setFormMinExp(0);
    setFormEdu("");
    setFormType("Full-time");
    setFormLocation("Remote / Hybrid");
    setFormStatus("active");
    setShowCreateModal(true);
  };

  const openEditModal = (job) => {
    setEditingJob(job);
    setFormTitle(job.title || "");
    setFormDept(job.department || "Engineering");
    setFormDesc(job.description || "");
    setFormResp(job.responsibilities || "");
    setFormReqSkills(Array.isArray(job.required_skills) ? job.required_skills : []);
    setFormPrefSkills(Array.isArray(job.preferred_skills) ? job.preferred_skills : []);
    setFormMinExp(job.min_experience_years || 0);
    setFormEdu(job.education_requirement || "");
    setFormType(job.employment_type || "Full-time");
    setFormLocation(job.location || "Remote / Hybrid");
    setFormStatus(job.status || "active");
    setShowCreateModal(true);
  };

  const handleAddReqSkill = () => {
    const val = formReqInput.trim().toLowerCase();
    if (val && !formReqSkills.includes(val)) {
      setFormReqSkills([...formReqSkills, val]);
      setFormReqInput("");
    }
  };

  const handleRemoveReqSkill = (skill) => {
    setFormReqSkills(formReqSkills.filter((s) => s !== skill));
  };

  const handleAddPrefSkill = () => {
    const val = formPrefInput.trim().toLowerCase();
    if (val && !formPrefSkills.includes(val)) {
      setFormPrefSkills([...formPrefSkills, val]);
      setFormPrefInput("");
    }
  };

  const handleRemovePrefSkill = (skill) => {
    setFormPrefSkills(formPrefSkills.filter((s) => s !== skill));
  };

  // Helper: auto-extract skills from job description text
  const handleAutoExtractSkills = async () => {
    if (!formDesc.trim()) {
      alert("Please paste or enter a job description first.");
      return;
    }
    setParsingSkills(true);
    try {
      const res = await fetch("/api/jobs/parse-requirements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: formDesc }),
      });
      const data = await res.json();
      if (data.required_skills?.length || data.preferred_skills?.length) {
        setFormReqSkills(data.required_skills || []);
        setFormPrefSkills(data.preferred_skills || []);
        alert(
          `Extracted ${data.required_skills.length} required and ${data.preferred_skills.length} preferred skills. Review and adjust them as needed.`
        );
      } else {
        alert("No specific technical skills were detected from vocabulary. You can add them manually.");
      }
    } catch (err) {
      alert("Failed to auto-extract skills: " + err.message);
    } finally {
      setParsingSkills(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formTitle.trim() || !formDesc.trim()) {
      alert("Job title and description are required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        title: formTitle.trim(),
        department: formDept.trim(),
        description: formDesc.trim(),
        responsibilities: formResp.trim(),
        required_skills: formReqSkills,
        preferred_skills: formPrefSkills,
        min_experience_years: parseFloat(formMinExp) || 0,
        education_requirement: formEdu.trim(),
        employment_type: formType,
        location: formLocation.trim(),
        status: formStatus,
      };

      if (editingJob) {
        await onUpdateJob(editingJob.id, payload);
      } else {
        await onCreateJob(payload);
      }
      setShowCreateModal(false);
      onRefresh();
    } catch (err) {
      alert("Error saving job opening: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filtered jobs list
  const filteredJobs = jobs.filter((job) => {
    const matchesSearch =
      !search ||
      job.title?.toLowerCase().includes(search.toLowerCase()) ||
      job.department?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || job.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">TALENT ACQUISITION WORKFLOW</div>
          <h2>Job Openings Management</h2>
          <p className="muted">
            Create, manage, and configure job criteria for candidate screening.
          </p>
        </div>
        <div className="header-actions">
          <button className="primary-button" onClick={openCreateModal}>
            <IconPlus size={16} /> Create Job Opening
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-bar surface-card mb-4">
        <div className="search-box">
          <IconSearch size={18} className="text-muted" />
          <input
            type="text"
            placeholder="Search by job title or department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="filter-select-group">
          <label>Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="paused">Paused</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <button className="icon-refresh-btn" onClick={onRefresh} title="Refresh jobs">
          <IconRefresh size={16} />
        </button>
      </div>

      {/* Jobs Table */}
      <div className="surface-card">
        {filteredJobs.length > 0 ? (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Job Title & Dept</th>
                  <th>Location & Type</th>
                  <th>Required Skills</th>
                  <th>Status</th>
                  <th>Applicants</th>
                  <th>Avg Score</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredJobs.map((job) => (
                  <tr key={job.id}>
                    <td>
                      <div className="job-title-cell">
                        <strong>{job.title}</strong>
                        <span className="muted small">{job.department}</span>
                      </div>
                    </td>
                    <td>
                      <div className="job-meta-cell">
                        <span>{job.location}</span>
                        <small className="muted">{job.employment_type}</small>
                      </div>
                    </td>
                    <td>
                      <div className="skill-chips-mini">
                        {(job.required_skills || []).slice(0, 4).map((sk) => (
                          <span key={sk} className="chip-tag matched">
                            {sk}
                          </span>
                        ))}
                        {(job.required_skills || []).length > 4 && (
                          <span className="chip-tag standard">
                            +{(job.required_skills || []).length - 4}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge ${job.status}`}>
                        {job.status?.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div className="metric-cell">
                        <strong>{job.total_applications || 0}</strong>
                        <small>candidates</small>
                      </div>
                    </td>
                    <td>
                      {job.average_score != null ? (
                        <span
                          className={`score-pill ${
                            job.average_score >= 70
                              ? "high"
                              : job.average_score >= 45
                              ? "medium"
                              : "low"
                          }`}
                        >
                          {job.average_score.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-muted small">N/A</span>
                      )}
                    </td>
                    <td>
                      <div className="action-buttons-group">
                        <button
                          className="btn-table-action"
                          onClick={() => onSelectJobForCandidates(job.id)}
                          title="View applicants pipeline"
                        >
                          <IconUsers size={14} /> Pipeline
                        </button>
                        <button
                          className="btn-table-action"
                          onClick={() => onSelectJobForUpload(job.id)}
                          title="Upload and screen resumes for this job"
                        >
                          <IconUpload size={14} /> Screen
                        </button>
                        <button
                          className="btn-table-action secondary"
                          onClick={() => openEditModal(job)}
                          title="Edit job requirements"
                        >
                          Edit
                        </button>
                        <button
                          className="btn-table-action secondary"
                          onClick={() => onRescreenJob(job.id)}
                          title="Re-screen all candidates with updated criteria"
                        >
                          <IconRefresh size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <IconBriefcase size={36} className="text-muted" />
            <h4>No Job Openings Found</h4>
            <p className="muted">
              {search
                ? "No jobs match your search query."
                : "Create your first job opening to start screening resumes."}
            </p>
            <button className="primary-button mt-3" onClick={openCreateModal}>
              <IconPlus size={16} /> Create Job Opening
            </button>
          </div>
        )}
      </div>

      {/* Create / Edit Job Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-container modal-wide" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingJob ? "Edit Job Opening" : "Create New Job Opening"}</h3>
              <button
                className="icon-close-btn"
                onClick={() => setShowCreateModal(false)}
              >
                <IconX size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="modal-body-scrollable">
              <div className="form-grid-2">
                <div className="form-field">
                  <label>Job Title *</label>
                  <input
                    type="text"
                    required
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    placeholder="e.g. Junior Software Developer"
                  />
                </div>
                <div className="form-field">
                  <label>Department / Category</label>
                  <input
                    type="text"
                    value={formDept}
                    onChange={(e) => setFormDept(e.target.value)}
                    placeholder="e.g. Engineering, Analytics, IT"
                  />
                </div>
              </div>

              <div className="form-grid-3">
                <div className="form-field">
                  <label>Employment Type</label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value)}
                  >
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Contract">Contract</option>
                    <option value="Internship">Internship</option>
                  </select>
                </div>
                <div className="form-field">
                  <label>Location / Work Arrangement</label>
                  <input
                    type="text"
                    value={formLocation}
                    onChange={(e) => setFormLocation(e.target.value)}
                    placeholder="e.g. Remote / Hybrid / On-site"
                  />
                </div>
                <div className="form-field">
                  <label>Status</label>
                  <select
                    value={formStatus}
                    onChange={(e) => setFormStatus(e.target.value)}
                  >
                    <option value="active">Active</option>
                    <option value="paused">Paused</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>

              <div className="form-field">
                <div className="field-header-row">
                  <label>Job Description *</label>
                  <button
                    type="button"
                    className="btn-helper-sparkle"
                    onClick={handleAutoExtractSkills}
                    disabled={parsingSkills}
                    title="Analyzes description and detects required & preferred skills for your review"
                  >
                    <IconSparkles size={14} />{" "}
                    {parsingSkills ? "Detecting..." : "Auto-Extract Skills from Description"}
                  </button>
                </div>
                <textarea
                  rows={5}
                  required
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  placeholder="Paste complete job description, responsibilities, and qualifications..."
                />
              </div>

              {/* Required Skills Configurator */}
              <div className="form-field">
                <label>
                  Required Skills <span className="text-indigo">(Weight 2 in Matching)</span>
                </label>
                <div className="chips-input-box">
                  <div className="chips-wrap">
                    {formReqSkills.map((skill) => (
                      <span key={skill} className="skill-chip-edit required">
                        {skill}
                        <button
                          type="button"
                          onClick={() => handleRemoveReqSkill(skill)}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="add-chip-inline">
                    <input
                      type="text"
                      placeholder="Add required skill (e.g. python, sql, react)..."
                      value={formReqInput}
                      onChange={(e) => setFormReqInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddReqSkill();
                        }
                      }}
                    />
                    <button
                      type="button"
                      className="btn-add-chip"
                      onClick={handleAddReqSkill}
                    >
                      + Add
                    </button>
                  </div>
                </div>
              </div>

              {/* Preferred Skills Configurator */}
              <div className="form-field">
                <label>
                  Preferred Skills <span className="text-muted">(Weight 1 in Matching)</span>
                </label>
                <div className="chips-input-box">
                  <div className="chips-wrap">
                    {formPrefSkills.map((skill) => (
                      <span key={skill} className="skill-chip-edit preferred">
                        {skill}
                        <button
                          type="button"
                          onClick={() => handleRemovePrefSkill(skill)}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="add-chip-inline">
                    <input
                      type="text"
                      placeholder="Add preferred skill (e.g. machine learning, docker)..."
                      value={formPrefInput}
                      onChange={(e) => setFormPrefInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddPrefSkill();
                        }
                      }}
                    />
                    <button
                      type="button"
                      className="btn-add-chip"
                      onClick={handleAddPrefSkill}
                    >
                      + Add
                    </button>
                  </div>
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-field">
                  <label>Minimum Relevant Experience (Years)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    value={formMinExp}
                    onChange={(e) => setFormMinExp(e.target.value)}
                    placeholder="0 for entry level"
                  />
                </div>
                <div className="form-field">
                  <label>Education Requirements (Only if job-relevant)</label>
                  <input
                    type="text"
                    value={formEdu}
                    onChange={(e) => setFormEdu(e.target.value)}
                    placeholder="e.g. BS in CS, Analytics, or practical equivalent"
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-button"
                  disabled={isSubmitting}
                >
                  {isSubmitting
                    ? "Saving..."
                    : editingJob
                    ? "Save Changes"
                    : "Create Job Opening"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
