/** @format */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createCase } from "../services/caseService";

export default function CreateCasePage() {
  const navigate = useNavigate();

  const [caseName, setCaseName] = useState("");
  const [bodyLocation, setBodyLocation] = useState("");
  const [imageSource, setImageSource] = useState("mobile");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading) return;

    setLoading(true);
    setError("");

    try {
      const createdCase = await createCase({
        case_label: caseName.trim() || null,
        body_location: bodyLocation.trim() || null,
        image_source: imageSource.trim() || null,
      });

      navigate(`/cases/${createdCase.id}`);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to create case. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="mb-6 text-sm font-medium text-cyan-700 hover:underline"
        >
          ← Back to Dashboard
        </button>

        <div className="mb-7">
          <p className="text-sm font-semibold text-cyan-700">
            DermAI Workspace
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Create a New Case
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Create a separate workspace to organize skin images and research
            observations for this case.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
        >
          <div className="space-y-2">
            <label
              htmlFor="caseName"
              className="block text-sm font-medium text-slate-700"
            >
              Case Name
            </label>
            <input
              id="caseName"
              value={caseName}
              onChange={(event) => setCaseName(event.target.value)}
              maxLength={100}
              placeholder="e.g. Skin Observation 001"
              disabled={loading}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-cyan-600 focus:ring-4 focus:ring-cyan-600/10 disabled:opacity-60"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="bodyLocation"
              className="block text-sm font-medium text-slate-700"
            >
              Body Location
            </label>
            <input
              id="bodyLocation"
              value={bodyLocation}
              onChange={(event) => setBodyLocation(event.target.value)}
              maxLength={100}
              placeholder="e.g. arm, leg, face (optional)"
              disabled={loading}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-cyan-600 focus:ring-4 focus:ring-cyan-600/10 disabled:opacity-60"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="imageSource"
              className="block text-sm font-medium text-slate-700"
            >
              Image Source
            </label>
            <select
              id="imageSource"
              value={imageSource}
              onChange={(event) => setImageSource(event.target.value)}
              disabled={loading}
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-cyan-600 focus:ring-4 focus:ring-cyan-600/10 disabled:opacity-60"
            >
              <option value="mobile">Mobile photo</option>
              <option value="clinical">Clinical photo</option>
              <option value="dermoscopic">Dermoscopic image</option>
              <option value="other">Other</option>
            </select>
          </div>

          {error && (
            <p
              role="alert"
              className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-cyan-700 px-5 py-3 font-semibold text-white transition hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Creating case..." : "Create Case & Open Workspace"}
          </button>

          <p className="text-xs leading-5 text-slate-500">
            This academic research prototype does not provide a confirmed
            medical diagnosis.
          </p>
        </form>
      </div>
    </main>
  );
}
