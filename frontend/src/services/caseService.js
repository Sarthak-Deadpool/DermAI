/** @format */

import apiClient from "../api/client";

// Create a new case
export async function createCase(caseData) {
  const response = await apiClient.post("/api/v1/cases", caseData);

  return response.data;
}

// Upload an image to an existing case
export async function uploadCaseImage(caseId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post(
    `/api/v1/cases/${caseId}/images`,
    formData,
    {
      headers: {
        "Content-Type": undefined,
      },
    },
  );

  return response.data;
}
