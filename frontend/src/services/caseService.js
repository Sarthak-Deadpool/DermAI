/** @format */

import apiClient from "../api/client";

export async function createCase(caseData) {
  const response = await apiClient.post("/api/v1/cases", caseData);
  return response.data;
}

export async function getCases() {
  const response = await apiClient.get("/api/v1/cases");
  return response.data;
}

export async function getCaseById(caseId) {
  if (!caseId) {
    throw new Error("caseId is required");
  }

  const response = await apiClient.get(
    `/api/v1/cases/${encodeURIComponent(caseId)}`,
  );

  return response.data;
}

export async function getPatientCases(patientId) {
  if (!patientId) {
    throw new Error("patientId is required");
  }

  const response = await apiClient.get(
    `/api/v1/cases/patient/${encodeURIComponent(patientId)}`,
  );

  return response.data;
}

export async function uploadCaseImage() {}
