import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  withCredentials: true,
  timeout: 30000,
  headers: { Accept: "application/json" },
});

let csrfToken = "";
let csrfPromise;
const unsafe = new Set(["post", "put", "patch", "delete"]);

export function setCsrfToken(value) { csrfToken = value || ""; }
export async function refreshCsrf() {
  if (!csrfPromise) {
    csrfPromise = api.get("/auth/csrf").then(({ data }) => {
      csrfToken = data.csrf_token;
      return csrfToken;
    }).finally(() => { csrfPromise = undefined; });
  }
  return csrfPromise;
}

api.interceptors.request.use(async (config) => {
  if (unsafe.has(config.method?.toLowerCase())) {
    if (!csrfToken) await refreshCsrf();
    config.headers["X-CSRF-Token"] = csrfToken;
  }
  return config;
});

export function errorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(" ");
  if (!error?.response) return "The API could not be reached. Check your connection and try again.";
  if (error.response.status === 401) return "Your session has expired. Sign in again to continue.";
  if (error.response.status === 403) return "This action is not available for your account.";
  return fallback;
}
