/** @format */

import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 15000,

  withCredentials: true,

  withXSRFToken: true,
  xsrfCookieName: "dermai_csrf_token",
  xsrfHeaderName: "X-CSRF-Token",

  headers: {
    "Content-Type": "application/json",
  },
});

export default apiClient;
