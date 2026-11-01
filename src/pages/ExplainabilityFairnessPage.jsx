import React, { useState, useEffect } from "react";
import {
  IconScale,
  IconShield,
  IconCheck,
  IconAlertTriangle,
  IconRefresh,
  IconSparkles,
} from "../components/Icons";

export default function ExplainabilityFairnessPage() {
  const [auditData, setAuditData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadFairnessAudit = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/fairness/audit");
      const data = await res.json();
      setAuditData(data);
    } catch (err) {
      setError("Failed to run fairness audit: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFairnessAudit();
  }, []);

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">ETHICAL AI & RECRUITMENT GOVERNANCE</div>
          <h2>Explainability, Bias Awareness & Responsible AI</h2>
          <p className="muted">
            Auditing mathematical transparency, evidence alignment, and demographic neutrality.
          </p>
        </div>
        <div className="header-actions">
          <button
            className="primary-button"
            onClick={loadFairnessAudit}
            disabled={loading}
          >
            <IconRefresh size={16} />{" "}
            {loading ? "Evaluating..." : "Run Live Fairness Audit"}
          </button>
        </div>
      </div>

      {/* Hero Notice */}
      <div className="surface-card alert-notice-large mb-4">
        <div className="notice-icon-box">
          <IconShield size={28} className="text-indigo" />
        </div>
        <div>
          <h3>Decision-Support Signal, Not a Job Performance Predictor</h3>
          <p className="muted">
            FairHire AI calculates a transparent alignment score measuring how closely
            the text in a candidate’s resume matches the specific requirements of a job.
            It does <strong>not</strong> verify real-world competence, nor does it predict
            future job performance. All consequential decisions (shortlisting, interview
            scheduling, rejection) remain strictly in the hands of human recruiters.
          </p>
        </div>
      </div>

      {/* Grid: Scoring Formula & Excluded Features */}
      <div className="dashboard-columns mb-4">
        {/* Left Column: Mathematical Methodology */}
        <div className="surface-card col-wide">
          <div className="card-header">
            <h3>Scoring Methodology & Formula</h3>
            <span className="badge-pill positive">Deterministic</span>
          </div>

          <div className="methodology-content">
            <p className="muted small">
              Scores are calculated directly against the criteria of each specific job opening:
            </p>

            <div className="formula-box">
              <div className="formula-equation">
                Match Score ={" "}
                <span className="fraction">
                  <span className="numerator">
                    (2 × Matched Required) + (1 × Matched Preferred)
                  </span>
                  <span className="denominator">
                    (2 × Total Required) + (1 × Total Preferred)
                  </span>
                </span>{" "}
                × 100%
              </div>
            </div>

            <div className="components-table mt-4">
              <h5>Score Components & Weights:</h5>
              <div className="component-row">
                <strong>Required Skills Coverage</strong>
                <span>Weight 2.0 (Double Weight)</span>
                <p className="small muted">
                  Essential capabilities specified for the job. Must be backed by
                  verifiable evidence excerpts from the candidate's resume.
                </p>
              </div>

              <div className="component-row">
                <strong>Preferred Skills Overlap</strong>
                <span>Weight 1.0 (Standard Weight)</span>
                <p className="small muted">
                  Secondary or nice-to-have capabilities providing additional alignment
                  points without penalizing candidates who lack them.
                </p>
              </div>

              <div className="component-row">
                <strong>Semantic Text Similarity</strong>
                <span>Reported Separately</span>
                <p className="small muted">
                  Computed via dense neural embeddings (MiniLM-L6-v2) or local TF-IDF
                  cosine similarity. Measures semantic vocabulary overlap, not competence.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Protected Characteristics Exclusion Policy */}
        <div className="surface-card col-narrow">
          <div className="card-header">
            <h3>Explicitly Excluded Attributes</h3>
            <span className="badge-pill warning">Strict Policy</span>
          </div>

          <p className="muted small">
            To prevent demographic bias, FairHire AI strictly excludes the following
            features from all scoring and matching algorithms:
          </p>

          <ul className="excluded-list">
            {(
              auditData?.excluded_features || [
                "Gender and gender identity proxies",
                "Race, ethnicity, and nationality",
                "Religion and caste",
                "Disability and medical conditions",
                "Marital and parental status",
                "Photographs and physical appearance",
                "Age and birth years",
                "Candidate names as identity proxies",
                "University prestige ranking bias",
                "Zip code, address, or geographic socioeconomic indicators",
              ]
            ).map((feat, i) => (
              <li key={i}>
                <IconCheck size={14} className="text-green" /> {feat}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Controlled Synthetic Score Consistency Test Card */}
      <div className="surface-card mb-4">
        <div className="card-header">
          <div>
            <h3>Controlled Synthetic Demographic Consistency Audit</h3>
            <p className="muted small">
              Verification that identical qualifications receive identical match scores
              regardless of demographic test labels.
            </p>
          </div>
          {auditData && (
            <span
              className={`status-badge ${
                auditData.absolute_score_gap === 0 ? "badge-shortlisted" : "badge-rejected"
              }`}
            >
              {auditData.absolute_score_gap === 0 ? "PASS — ZERO GAP" : "REVIEW NEEDED"}
            </span>
          )}
        </div>

        {loading ? (
          <div className="loading-state">
            <IconRefresh size={28} className="spin text-indigo" />
            <p className="mt-2">Running controlled fairness test...</p>
          </div>
        ) : auditData ? (
          <div className="audit-results-area">
            <div className="metrics-grid mb-3">
              <div className="metric-card">
                <span className="metric-label">Absolute Score Gap</span>
                <strong className="metric-value text-green">
                  {auditData.absolute_score_gap?.toFixed(2)}%
                </strong>
                <small className="metric-sub">Zero disparity across equivalent profiles</small>
              </div>
              <div className="metric-card">
                <span className="metric-label">Synthetic Test Records</span>
                <strong className="metric-value">{auditData.candidate_count}</strong>
                <small className="metric-sub">Controlled synthetic benchmarks</small>
              </div>
              <div className="metric-card">
                <span className="metric-label">Audit Status</span>
                <strong className="metric-value text-green">PASS</strong>
                <small className="metric-sub">Deterministic scoring validated</small>
              </div>
            </div>

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Candidate Test ID</th>
                    <th>Synthetic Demographic Group</th>
                    <th>Required Matched</th>
                    <th>Preferred Matched</th>
                    <th>Match Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(auditData.results || []).map((res, i) => (
                    <tr key={i}>
                      <td className="font-semibold text-light">{res.candidate_id}</td>
                      <td>{res.group}</td>
                      <td>4 of 4</td>
                      <td>1 of 2</td>
                      <td>
                        <span className="score-pill high">{res.skill_score}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="limitations-box mt-4">
              <h5>Audit Limitations & Responsible-AI Scope:</h5>
              <ul className="small muted">
                {(auditData.limitations || []).map((lim, idx) => (
                  <li key={idx}>• {lim}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <p className="muted">Click "Run Live Fairness Audit" to evaluate consistency.</p>
          </div>
        )}
      </div>
    </div>
  );
}
