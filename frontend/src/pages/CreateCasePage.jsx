/** @format */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ClipboardPlus, LoaderCircle } from "lucide-react";
import Sidebar from "../components/sidebar/Sidebar";
import { createCase } from "../services/caseService";

const initialForm = {
  patient_id: "",
  case_label: "",
  description: "",
  body_location: "",
  image_source: "mobile_camera",
};

export default function CreateCasePage() {
  const navigate = useNavigate();

  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!form.patient_id.trim()) {
      setError("Patient ID is required.");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        patient_id: form.patient_id.trim(),
        case_label: form.case_label.trim() || null,
        description: form.description.trim() || null,
        body_location: form.body_location.trim() || null,
        image_source: form.image_source || null,
      };

      await createCase(payload);
      navigate("/my-cases", {
        replace: true,
        state: { message: "Case created successfully." },
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Unable to create the case. Check the patient ID and try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  const inputClass =
    "mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10";

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar role="user" />

      <main className="min-h-screen px-5 py-8 md:ml-64 md:px-8">
        <div className="mx-auto max-w-3xl">
          <Link
            to="/my-cases"
            className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-teal-700"
          >
            <ArrowLeft size={17} />
            Back to My Cases
          </Link>

          <div className="mb-7 flex items-start gap-4">
            <div className="rounded-2xl bg-teal-50 p-3 text-teal-700">
              <ClipboardPlus size={26} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                Create New Case
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Create a case record before adding skin images or analyses.
              </p>
            </div>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:p-8"
          >
            {error && (
              <div
                role="alert"
                className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                {error}
              </div>
            )}

            <div className="space-y-5">
              <div>
                <label
                  htmlFor="patient_id"
                  className="text-sm font-semibold text-slate-700"
                >
                  Patient ID <span className="text-red-500">*</span>
                </label>
                <input
                  id="patient_id"
                  name="patient_id"
                  value={form.patient_id}
                  onChange={handleChange}
                  placeholder="Enter an existing patient UUID"
                  className={inputClass}
                  required
                />
                <p className="mt-1.5 text-xs text-slate-500">
                  Use the ID of a patient that already exists in your database.
                </p>
              </div>

              <div>
                <label
                  htmlFor="case_label"
                  className="text-sm font-semibold text-slate-700"
                >
                  Case Name
                </label>
                <input
                  id="case_label"
                  name="case_label"
                  value={form.case_label}
                  onChange={handleChange}
                  maxLength={100}
                  placeholder="e.g. Skin lesion — left forearm"
                  className={inputClass}
                />
              </div>

              <div>
                <label
                  htmlFor="body_location"
                  className="text-sm font-semibold text-slate-700"
                >
                  Body Location
                </label>
                <select
                  id="body_location"
                  name="body_location"
                  value={form.body_location}
                  onChange={handleChange}
                  className={inputClass}
                >
                  <option value="">Select a location</option>
                  {[
                    "Face",
                    "Scalp",
                    "Neck",
                    "Chest",
                    "Back",
                    "Arm",
                    "Forearm",
                    "Hand",
                    "Leg",
                    "Foot",
                    "Other",
                  ].map((location) => (
                    <option key={location} value={location}>
                      {location}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="image_source"
                  className="text-sm font-semibold text-slate-700"
                >
                  Intended Image Source
                </label>
                <select
                  id="image_source"
                  name="image_source"
                  value={form.image_source}
                  onChange={handleChange}
                  className={inputClass}
                >
                  <option value="mobile_camera">Mobile camera</option>
                  <option value="gallery_upload">Gallery upload</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="description"
                  className="text-sm font-semibold text-slate-700"
                >
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  rows={4}
                  placeholder="Optional notes about this case..."
                  className={`${inputClass} resize-y`}
                />
              </div>
            </div>

            <div className="mt-8 flex flex-col-reverse gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:justify-end">
              <Link
                to="/my-cases"
                className="rounded-xl border border-slate-200 px-5 py-3 text-center text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
              >
                Cancel
              </Link>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-teal-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading && <LoaderCircle size={17} className="animate-spin" />}
                {loading ? "Creating Case..." : "Create Case"}
              </button>
            </div>
          </form>

          <p className="mt-4 text-xs leading-5 text-slate-500">
            Creating a case only saves its basic information. Image upload and
            AI analysis will be separate steps.
          </p>
        </div>
      </main>
    </div>
  );
}
