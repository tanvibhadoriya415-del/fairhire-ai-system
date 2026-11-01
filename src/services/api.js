const API_BASE = "/api";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = { ...options.headers };

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("text/csv")) {
    if (!response.ok) throw new Error("CSV download failed");
    return response.blob();
  }

  let data;
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    const errorMsg =
      typeof data.detail === "string"
        ? data.detail
        : data.message || `Request failed with status ${response.status}`;
    throw new Error(errorMsg);
  }

  return data;
}

export const api = {
  // Dashboard
  getStats: () => request("/dashboard/stats"),

  // Jobs
  getJobs: (search = "", status = "") => {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (status && status !== "all") params.append("status", status);
    const query = params.toString();
    return request(`/jobs${query ? `?${query}` : ""}`);
  },
  getJob: (jobId) => request(`/jobs/${jobId}`),
  createJob: (payload) =>
    request("/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateJob: (jobId, payload) =>
    request(`/jobs/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  parseRequirements: (description) =>
    request("/jobs/parse-requirements", {
      method: "POST",
      body: JSON.stringify({ description }),
    }),
  rescreenJob: (jobId) =>
    request(`/jobs/${jobId}/rescreen`, {
      method: "POST",
    }),

  // Resumes & Screening
  uploadResumes: (jobId, files) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    return request(`/jobs/${jobId}/screen`, {
      method: "POST",
      body: formData,
    });
  },

  // Candidates & Applications
  getCandidates: (jobId, filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== "" && val !== "all") {
        params.append(key, val);
      }
    });
    const query = params.toString();
    return request(`/jobs/${jobId}/candidates${query ? `?${query}` : ""}`);
  },
  getApplication: (appId) => request(`/applications/${appId}`),
  updateStatus: (appId, status, note = "") =>
    request(`/applications/${appId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, note }),
    }),
  updateNotes: (appId, notes) =>
    request(`/applications/${appId}/notes`, {
      method: "PATCH",
      body: JSON.stringify({ notes }),
    }),
  getApplicationHistory: (appId) => request(`/applications/${appId}/history`),

  // Export
  exportCsvUrl: (jobId) => `${API_BASE}/jobs/${jobId}/export.csv`,

  // Fairness & Audit
  getFairnessAudit: () => request("/fairness/audit"),
  getAuditEvents: (limit = 50) => request(`/audit/events?limit=${limit}`),

  // Demo Seeding
  seedDemo: () =>
    request("/demo/seed", {
      method: "POST",
    }),
};
