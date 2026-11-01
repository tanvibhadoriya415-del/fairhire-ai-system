import React, { useState, useEffect } from "react";
import {
  IconHistory,
  IconClock,
  IconRefresh,
  IconShield,
  IconCheck,
  IconAlertTriangle,
} from "../components/Icons";

export default function AuditHistoryPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchEvents = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/audit/events?limit=100");
      const data = await res.json();
      setEvents(data.events || []);
    } catch (err) {
      setError("Failed to load audit history: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const getEventBadge = (type) => {
    switch (type) {
      case "screening_batch":
        return { label: "BATCH SCREENING", cls: "badge-interview" };
      case "status_changed":
        return { label: "STATUS CHANGE", cls: "badge-shortlisted" };
      case "job_created":
        return { label: "JOB CREATED", cls: "badge-review" };
      case "job_updated":
        return { label: "JOB UPDATED", cls: "badge-review" };
      case "re_screen":
        return { label: "RE-SCREENING", cls: "badge-offer" };
      default:
        return { label: type.toUpperCase(), cls: "badge-applied" };
    }
  };

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">SYSTEM LOGS & COMPLIANCE TRAIL</div>
          <h2>Screening & Audit History</h2>
          <p className="muted">
            Chronological audit log tracking batch screening events, status changes,
            and criteria modifications.
          </p>
        </div>
        <div className="header-actions">
          <button className="icon-refresh-btn" onClick={fetchEvents} title="Refresh audit log">
            <IconRefresh size={16} />
          </button>
        </div>
      </div>

      <div className="surface-card">
        {loading ? (
          <div className="loading-state">
            <IconRefresh size={28} className="spin text-indigo" />
            <p className="mt-2">Loading audit trail...</p>
          </div>
        ) : events.length > 0 ? (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Event Type</th>
                  <th>Job Opening</th>
                  <th>Details & Changes</th>
                  <th>Actor</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => {
                  const badge = getEventBadge(ev.event_type);
                  return (
                    <tr key={ev.id}>
                      <td>
                        <span className={`status-badge ${badge.cls}`}>{badge.label}</span>
                      </td>
                      <td className="font-semibold text-light">
                        {ev.job_title || `Job ID ${ev.job_id || "N/A"}`}
                      </td>
                      <td className="small text-muted">
                        {ev.event_type === "status_changed" ? (
                          <span>
                            Transitioned from <strong>{ev.details?.previous || "none"}</strong> to{" "}
                            <strong className="text-light">{ev.details?.new}</strong>
                            {ev.details?.note && (
                              <span className="block italic text-gray">“{ev.details.note}”</span>
                            )}
                          </span>
                        ) : ev.event_type === "screening_batch" ? (
                          <span>
                            Processed <strong>{ev.details?.processed || 0}</strong> resumes (
                            {ev.details?.failed || 0} failed)
                          </span>
                        ) : (
                          <span>{JSON.stringify(ev.details || {})}</span>
                        )}
                      </td>
                      <td>
                        <span className="text-muted small">{ev.actor || "HR Recruiter"}</span>
                      </td>
                      <td className="text-muted small">{ev.created_at}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <IconHistory size={36} className="text-muted" />
            <h4>No Audit Events Recorded Yet</h4>
            <p className="muted">Screening and recruitment activities will appear here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
