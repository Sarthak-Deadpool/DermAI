/** @format */

import apiClient from "../api/client";

// ============================================
// General User: Own Patient Profile
// ============================================

/**
 * Create the authenticated user's patient profile.
 * POST /api/v1/patients/me
 */
export async function createMyPatient(patientData) {
  const response = await apiClient.post("/api/v1/patients/me", patientData);

  return response.data;
}

/**
 * Get the authenticated user's patient profile.
 * GET /api/v1/patients/me
 */
export async function getMyPatient() {
  const response = await apiClient.get("/api/v1/patients/me");
  return response.data;
}

/**
 * Update the authenticated user's patient profile.
 * PATCH /api/v1/patients/me
 */
export async function updateMyPatient(patientData) {
  const response = await apiClient.patch("/api/v1/patients/me", patientData);

  return response.data;
}

/**
 * Delete the authenticated user's patient profile.
 * DELETE /api/v1/patients/me
 */
export async function deleteMyPatient() {
  await apiClient.delete("/api/v1/patients/me");
}

// ============================================
// Clinician: Patient Management
// ============================================

/**
 * Create a patient record.
 * POST /api/v1/patients/
 */
export async function createPatient(patientData) {
  const response = await apiClient.post("/api/v1/patients/", patientData);

  return response.data;
}

/**
 * Get all patients accessible to the clinician.
 * GET /api/v1/patients/
 */
export async function getPatients() {
  const response = await apiClient.get("/api/v1/patients/");
  return response.data;
}

/**
 * Get a patient by ID.
 * GET /api/v1/patients/{patient_id}
 */
export async function getPatientById(patientId) {
  if (!patientId) {
    throw new Error("patientId is required");
  }

  const response = await apiClient.get(
    `/api/v1/patients/${encodeURIComponent(patientId)}`,
  );

  return response.data;
}

/**
 * Update a patient record.
 * PATCH /api/v1/patients/{patient_id}
 */
export async function updatePatient(patientId, patientData) {
  if (!patientId) {
    throw new Error("patientId is required");
  }

  const response = await apiClient.patch(
    `/api/v1/patients/${encodeURIComponent(patientId)}`,
    patientData,
  );

  return response.data;
}

/**
 * Delete a patient record.
 * DELETE /api/v1/patients/{patient_id}
 */
export async function deletePatient(patientId) {
  if (!patientId) {
    throw new Error("patientId is required");
  }

  await apiClient.delete(`/api/v1/patients/${encodeURIComponent(patientId)}`);
}
