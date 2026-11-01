import React, { useState, useEffect, useCallback } from "react";
import "./App.css";
import {
  IconDashboard,
  IconBriefcase,
  IconUpload,
  IconUsers,
  IconScale,
  IconHistory,
  IconSparkles,
} from "./components/Icons";
import { api } from "./services/api";
import DashboardPage from "./pages/DashboardPage";
import JobManagementPage from "./pages/JobManagementPage";
import ResumeUploadPage from "./pages/ResumeUploadPage";
import CandidateExplorerPage from "./pages/CandidateExplorerPage";
import ExplainabilityFairnessPage from "./pages/ExplainabilityFairnessPage";
import AuditHistoryPage from "./pages/AuditHistoryPage";
import CandidateDetailDrawer from "./components/CandidateDetailDrawer";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: IconDashboard },
  { id: "jobs", label: "Job Openings", icon: IconBriefcase },
  { id: "upload", label: "Screen Resumes", icon: IconUpload },
  { id: "candidates", label: "Candidate Explorer", icon: IconUsers },
  { id: "fairness", label: "Explainability & Bias", icon: IconScale },
  { id: "history", label: "Audit Trail", icon: IconHistory },
];

export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [activeApplication, setActiveApplication] = useState(null);
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type = "success") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4500);
  };

  const loadInitialData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsData, jobsData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getJobs().catch(() => ({ jobs: [] })),
      ]);

      setStats(statsData);
      const jobsList = jobsData.jobs || [];
      setJobs(jobsList);

      if (jobsList.length > 0 && !selectedJobId) {
        setSelectedJobId(String(jobsList[0].id));
      }
    } catch (err) {
      console.error("Initial load failed:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedJobId]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleSelectCandidate = async (applicationId) => {
    try {
      const res = await api.getApplication(applicationId);
      setActiveApplication(res.application);
    } catch (err) {
      alert("Failed to load candidate profile: " + err.message);
    }
  };

  const handleStatusChange = async (applicationId, newStatus, note = "") => {
    const res = await api.updateStatus(applicationId, newStatus, note);
    setActiveApplication(res.application);
    showNotification(`Candidate status updated to ${newStatus.replace("_", " ").toUpperCase()}`);
    loadInitialData();
  };

  const handleNotesChange = async (applicationId, notes) => {
    const res = await api.updateNotes(applicationId, notes);
    setActiveApplication(res.application);
    showNotification("HR notes updated successfully");
  };

  const handleSeedDemo = async () => {
    setSeeding(true);
    try {
      const res = await api.seedDemo();
      showNotification(
        `Demo data seeded successfully! Created jobs: ${res.jobs_created.join(", ")} with synthetic applicants.`
      );
      await loadInitialData();
      if (jobs.length > 0) {
        setSelectedJobId(String(jobs[0].id));
      }
    } catch (err) {
      alert("Demo seeding failed: " + err.message);
    } finally {
      setSeeding(false);
    }
  };

  const handleCreateJob = async (payload) => {
    const res = await api.createJob(payload);
    showNotification(`Job opening '${res.job.title}' created successfully.`);
    await loadInitialData();
    setSelectedJobId(String(res.job.id));
  };

  const handleUpdateJob = async (jobId, payload) => {
    const res = await api.updateJob(jobId, payload);
    showNotification(`Job opening '${res.job.title}' updated.`);
    await loadInitialData();
  };

  const handleRescreenJob = async (jobId) => {
    try {
      const res = await api.rescreenJob(jobId);
      showNotification(
        `Re-screening complete. ${res.rescreened_count} candidates evaluated under new criteria.`
      );
      loadInitialData();
    } catch (err) {
      alert("Re-screening failed: " + err.message);
    }
  };

  const handleSelectJobForCandidates = (jobId) => {
    setSelectedJobId(String(jobId));
    setCurrentPage("candidates");
  };

  const handleSelectJobForUpload = (jobId) => {
    setSelectedJobId(String(jobId));
    setCurrentPage("upload");
  };

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">FH</div>
          <div>
            <h1 className="brand-title">FairHire AI</h1>
            <span className="brand-badge">HR SaaS</span>
          </div>
        </div>

        <div className="sidebar-nav-label">RECRUITMENT WORKSPACE</div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                className={`nav-button ${isActive ? "active" : ""}`}
                onClick={() => setCurrentPage(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
                {item.id === "candidates" && stats?.total_applications > 0 && (
                  <span className="nav-counter">{stats.total_applications}</span>
                )}
                {item.id === "jobs" && stats?.active_jobs > 0 && (
                  <span className="nav-counter">{stats.active_jobs}</span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <button
            className="sidebar-seed-btn"
            onClick={handleSeedDemo}
            disabled={seeding}
            title="Seed sample jobs and synthetic applicants for full end-to-end testing"
          >
            <IconSparkles size={16} />
            <span>{seeding ? "Seeding Data..." : "Load Demo HR Data"}</span>
          </button>
          <div className="system-status-indicator mt-3">
            <span className="live-dot" />
            <small>Local SQLite DB Connected</small>
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <main className="main-content">
        {/* Global Toast Notification */}
        {notification && (
          <div className={`toast-notification ${notification.type}`}>
            <span>{notification.message}</span>
            <button onClick={() => setNotification(null)}>×</button>
          </div>
        )}

        {currentPage === "dashboard" && (
          <DashboardPage
            stats={stats}
            loading={loading}
            onNavigate={setCurrentPage}
            onSelectCandidate={handleSelectCandidate}
            onSeedDemo={handleSeedDemo}
            seeding={seeding}
          />
        )}

        {currentPage === "jobs" && (
          <JobManagementPage
            jobs={jobs}
            loading={loading}
            onRefresh={loadInitialData}
            onCreateJob={handleCreateJob}
            onUpdateJob={handleUpdateJob}
            onSelectJobForCandidates={handleSelectJobForCandidates}
            onSelectJobForUpload={handleSelectJobForUpload}
            onRescreenJob={handleRescreenJob}
          />
        )}

        {currentPage === "upload" && (
          <ResumeUploadPage
            jobs={jobs}
            selectedJobId={selectedJobId}
            onSelectJob={setSelectedJobId}
            onNavigate={setCurrentPage}
            onSelectCandidate={handleSelectCandidate}
          />
        )}

        {currentPage === "candidates" && (
          <CandidateExplorerPage
            jobs={jobs}
            selectedJobId={selectedJobId}
            onSelectJob={setSelectedJobId}
            onSelectCandidate={handleSelectCandidate}
            onStatusChange={handleStatusChange}
          />
        )}

        {currentPage === "fairness" && <ExplainabilityFairnessPage />}

        {currentPage === "history" && <AuditHistoryPage />}

        {/* Candidate Detail Drawer */}
        {activeApplication && (
          <CandidateDetailDrawer
            application={activeApplication}
            onClose={() => setActiveApplication(null)}
            onStatusChange={handleStatusChange}
            onNotesChange={handleNotesChange}
          />
        )}
      </main>
    </div>
  );
}
