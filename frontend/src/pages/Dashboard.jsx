/** @format */

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";

export default function DashboardPage() {
  const navigate = useNavigate();

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchCases = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.get("/api/v1/cases");
      const data = response.data;

      const caseList = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
          ? data.items
          : Array.isArray(data?.cases)
            ? data.cases
            : [];

      setCases(caseList);
    } catch (err) {
      setError(
        err.response?.status === 401 || err.response?.status === 403
          ? "Your session may have expired. Please log in again."
          : "Unable to load cases. Please check your backend connection.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const recentCases = [...cases]
    .sort(
      (a, b) =>
        new Date(b.created_at || 0).getTime() -
        new Date(a.created_at || 0).getTime(),
    )
    .slice(0, 5);

  const formatDate = (date) => {
    if (!date) return "—";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) return "—";

    return parsedDate.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="text-left"
          >
            <span className="text-2xl font-bold tracking-tight text-cyan-700">
              DermAI
            </span>
            <span className="mt-0.5 block text-xs text-slate-500">
              Skin Research & Case Management
            </span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/create-case")}
            className="rounded-lg bg-cyan-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-cyan-800"
          >
            + Create New Case
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        {/* Welcome section */}
        <section className="mb-8">
          <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-700">
            Workspace
          </p>

          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Dashboard
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Manage skin image cases and organize research records in one place.
          </p>
        </section>

        {/* Overview cards */}
        <section className="mb-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Total Cases</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">
              {loading ? "—" : cases.length}
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Cases available in your account
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Recent Cases</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">
              {loading ? "—" : recentCases.length}
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Latest five case records
            </p>
          </div>

          <div className="rounded-2xl border border-cyan-100 bg-cyan-50 p-6 shadow-sm">
            <p className="text-sm font-medium text-cyan-800">Quick Action</p>
            <h2 className="mt-3 text-xl font-bold text-slate-900">
              Start a New Case
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Create a case and upload a skin image.
            </p>
            <button
              type="button"
              onClick={() => navigate("/create-case")}
              className="mt-4 font-semibold text-cyan-800 hover:text-cyan-950"
            >
              Get started →
            </button>
          </div>
        </section>

        {/* Case list */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-6 py-5">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Recent Cases</h2>
              <p className="mt-1 text-sm text-slate-500">
                Review your latest case records.
              </p>
            </div>

            <button
              type="button"
              onClick={fetchCases}
              disabled={loading}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {loading ? "Loading..." : "↻ Refresh"}
            </button>
          </div>

          {error && (
            <div className="m-5 rounded-lg border border-red-200 bg-red-50 p-4">
              <p role="alert" className="text-sm text-red-700">
                {error}
              </p>
              <button
                type="button"
                onClick={fetchCases}
                className="mt-2 text-sm font-semibold text-red-800 underline"
              >
                Try again
              </button>
            </div>
          )}

          {loading ? (
            <div className="px-6 py-16 text-center">
              <p className="text-sm text-slate-500">Loading case records...</p>
            </div>
          ) : !error && cases.length === 0 ? (
            <div className="px-6 py-16 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-cyan-50 text-2xl">
                +
              </div>
              <h3 className="mt-4 text-lg font-semibold text-slate-900">
                No cases yet
              </h3>
              <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">
                Your case records will appear here. Create your first case to
                get started.
              </p>
              <button
                type="button"
                onClick={() => navigate("/create-case")}
                className="mt-5 rounded-lg bg-cyan-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-cyan-800"
              >
                Create Your First Case
              </button>
            </div>
          ) : !error ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[650px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Case</th>
                    <th className="px-6 py-4 font-semibold">Body Location</th>
                    <th className="px-6 py-4 font-semibold">Image Source</th>
                    <th className="px-6 py-4 font-semibold">Created</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {recentCases.map((item, index) => (
                    <tr
                      key={item.id ?? index}
                      className="transition hover:bg-slate-50"
                    >
                      <td className="px-6 py-4">
                        <p className="font-semibold text-slate-900">
                          {item.case_label || `Case ${index + 1}`}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          ID: {item.id ?? "—"}
                        </p>
                      </td>

                      <td className="px-6 py-4 text-slate-600">
                        {item.body_location || "Not specified"}
                      </td>

                      <td className="px-6 py-4 text-slate-600">
                        {item.image_source || "—"}
                      </td>

                      <td className="px-6 py-4 text-slate-600">
                        {formatDate(item.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          <div className="border-t border-slate-200 px-6 py-4">
            <p className="text-xs leading-5 text-slate-500">
              DermAI is an academic research prototype. Case records and
              uploaded images are not confirmed medical diagnoses.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
