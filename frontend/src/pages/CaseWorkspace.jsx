/** @format */

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import apiClient from "../api/client";
import { uploadCaseImage } from "../services/caseService";
import ImageUpload from "../components/cases/ImageUpload";

export default function CaseWorkspacePage() {
  const { caseId } = useParams();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [loadingCase, setLoadingCase] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchCase = useCallback(async () => {
    setLoadingCase(true);
    setError("");

    try {
      const response = await apiClient.get(`/api/v1/cases/${caseId}`);
      setCaseData(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load this case. Check that it exists and you have access.",
      );
    } finally {
      setLoadingCase(false);
    }
  }, [caseId]);

  useEffect(() => {
    fetchCase();
  }, [fetchCase]);

  async function handleUpload(event) {
    event.preventDefault();
    if (!selectedImage || uploading) return;

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      const result = await uploadCaseImage(caseId, selectedImage);

      setUploadedImages((previous) => [result, ...previous]);
      setSelectedImage(null);
      setSuccess("Image uploaded successfully to this case.");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Image upload failed. Please try again.",
      );
    } finally {
      setUploading(false);
    }
  }

  if (loadingCase) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-600">Opening case workspace...</p>
      </main>
    );
  }

  if (!caseData) {
    return (
      <main className="min-h-screen bg-slate-50 p-6">
        <div className="mx-auto max-w-3xl rounded-2xl border border-red-200 bg-white p-6">
          <p role="alert" className="text-sm text-red-700">
            {error || "Case could not be found."}
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="mt-4 font-medium text-cyan-700 hover:underline"
          >
            Back to Dashboard
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4">
          <div>
            <p className="text-xl font-bold text-cyan-700">DermAI</p>
            <p className="text-xs text-slate-500">Case Workspace</p>
          </div>
          <button
            onClick={() => navigate("/dashboard")}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50"
          >
            ← All Cases
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-6 px-5 py-8 lg:grid-cols-[280px_minmax(0,1fr)]">
        {/* Case sidebar */}
        <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Current Case
          </p>
          <h1 className="mt-2 wrap-break-word text-xl font-bold text-slate-900">
            {caseData.case_label || `Case ${caseData.id}`}
          </h1>

          <p className="mt-2 break-all text-xs text-slate-500">
            Case ID: {caseData.id}
          </p>

          <div className="mt-5 space-y-3 border-t border-slate-100 pt-4 text-sm">
            <div>
              <p className="text-slate-500">Body location</p>
              <p className="mt-1 font-medium">
                {caseData.body_location || "Not specified"}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Image source</p>
              <p className="mt-1 font-medium">
                {caseData.image_source || "Not specified"}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Created</p>
              <p className="mt-1 font-medium">
                {caseData.created_at
                  ? new Date(caseData.created_at).toLocaleString()
                  : "—"}
              </p>
            </div>
          </div>
        </aside>

        {/* Main workspace */}
        <section className="min-w-0 space-y-6">
          <div>
            <p className="text-sm font-semibold text-cyan-700">
              Case conversation
            </p>
            <h2 className="mt-1 text-2xl font-bold text-slate-900">
              Images & Observations
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Upload an image to attach it to this case. Analysis and
              conversation features can be connected in a later milestone.
            </p>
          </div>

          <form
            onSubmit={handleUpload}
            className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"
          >
            <h3 className="font-semibold text-slate-900">
              Upload a skin image
            </h3>

            <ImageUpload
              onFileChange={(file) => {
                setSelectedImage(file);
                setError("");
                setSuccess("");
              }}
              disabled={uploading}
            />

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                {error}
              </p>
            )}

            {success && (
              <p
                role="status"
                className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700"
              >
                {success}
              </p>
            )}

            <button
              type="submit"
              disabled={!selectedImage || uploading}
              className="w-full rounded-xl bg-cyan-700 px-5 py-3 font-semibold text-white hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            >
              {uploading ? "Uploading image..." : "Upload to This Case"}
            </button>
          </form>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-semibold text-slate-900">Uploaded Images</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                {uploadedImages.length} this session
              </span>
            </div>

            {uploadedImages.length === 0 ? (
              <div className="mt-5 rounded-xl border border-dashed border-slate-300 px-5 py-10 text-center">
                <p className="font-medium text-slate-700">
                  No images uploaded in this session
                </p>
                <p className="mt-2 text-sm text-slate-500">
                  Uploaded image records will appear here.
                </p>
              </div>
            ) : (
              <div className="mt-5 space-y-3">
                {uploadedImages.map((image, index) => (
                  <div
                    key={image.id ?? index}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4"
                  >
                    <div className="min-w-0">
                      <p className="break-words font-medium text-slate-900">
                        {image.original_filename || "Uploaded image"}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {image.content_type || "Image"} ·{" "}
                        {typeof image.file_size === "number"
                          ? `${(image.file_size / 1024).toFixed(1)} KB`
                          : "Size unavailable"}
                      </p>
                    </div>
                    <span className="text-xs font-medium text-green-700">
                      Uploaded
                    </span>
                  </div>
                ))}
              </div>
            )}

            <p className="mt-5 text-xs leading-5 text-slate-500">
              DermAI is an academic research prototype. Uploaded images do not
              constitute a medical diagnosis.
            </p>
          </section>
        </section>
      </div>
    </main>
  );
}
