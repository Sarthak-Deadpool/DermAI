import { api } from "./client";

const data = (promise) => promise.then((response) => response.data);

export const authApi = {
  login: (payload) => data(api.post("/auth/login", payload)),
  register: (payload) => data(api.post("/auth/register", payload)),
  me: () => data(api.get("/auth/me")),
  updateMe: (payload) => data(api.patch("/auth/me", payload)),
  logout: () => data(api.post("/auth/logout")),
  sessions: () => data(api.get("/auth/sessions")),
  revokeSession: (id) => data(api.delete(`/auth/sessions/${encodeURIComponent(id)}`)),
  revokeOthers: () => data(api.post("/auth/sessions/revoke-others")),
  logoutAll: () => data(api.post("/auth/logout-all")),
};

export const patientApi = {
  list: (params = {}) => data(api.get("/api/v1/patients/", { params })),
  get: (id) => data(api.get(`/api/v1/patients/${encodeURIComponent(id)}`)),
  create: (payload) => data(api.post("/api/v1/patients/", payload)),
  update: (id, payload) => data(api.patch(`/api/v1/patients/${encodeURIComponent(id)}`, payload)),
  archive: (id) => data(api.delete(`/api/v1/patients/${encodeURIComponent(id)}`)),
  me: () => data(api.get("/api/v1/patients/me")),
  createMe: (payload) => data(api.post("/api/v1/patients/me", payload)),
  updateMe: (payload) => data(api.patch("/api/v1/patients/me", payload)),
};

export const caseApi = {
  list: (params = {}) => data(api.get("/api/v1/cases", { params })),
  forPatient: (patientId) => data(api.get(`/api/v1/cases/patient/${encodeURIComponent(patientId)}`)),
  get: (id) => data(api.get(`/api/v1/cases/${encodeURIComponent(id)}`)),
  create: (payload) => data(api.post("/api/v1/cases", payload)),
  updateStatus: (id, status) => data(api.patch(`/api/v1/cases/${encodeURIComponent(id)}/status`, { status })),
  notes: (id) => data(api.get(`/api/v1/cases/${encodeURIComponent(id)}/notes`)),
  addNote: (id, note) => data(api.post(`/api/v1/cases/${encodeURIComponent(id)}/notes`, { note })),
  events: (id) => data(api.get(`/api/v1/cases/${encodeURIComponent(id)}/events`)),
};

export const imageApi = {
  list: (caseId) => data(api.get(`/api/v1/cases/${encodeURIComponent(caseId)}/images`)),
  upload: (caseId, file, onUploadProgress) => {
    const form = new FormData(); form.append("file", file);
    return data(api.post(`/api/v1/cases/${encodeURIComponent(caseId)}/images`, form, { onUploadProgress }));
  },
  file: (caseId, imageId) => data(api.get(`/api/v1/cases/${encodeURIComponent(caseId)}/images/${encodeURIComponent(imageId)}/file`, { responseType: "blob" })),
  preprocessing: (caseId, imageId) => data(api.post(`/api/v1/cases/${encodeURIComponent(caseId)}/images/${encodeURIComponent(imageId)}/preprocessing`)),
};

export const adminApi = {
  users: () => data(api.get("/auth/admin/users")),
  updateUser: (id, payload) => data(api.patch(`/auth/admin/users/${encodeURIComponent(id)}`, payload)),
  audit: (params = {}) => data(api.get("/auth/admin/audit", { params })),
};
