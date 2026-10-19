/** @format */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileText,
  FolderOpen,
  Plus,
  RefreshCw,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import Sidebar from "../components/sidebar/Sidebar";
import { getCases } from "../services/caseService";

function formatDate(value) {
  if (!value) return "Date unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function getCaseId(item) {
  return item.case_id ?? item.caseId ?? item.id ?? item._id;
}

function getCaseTitle(item) {
  return (
    item.title ??
    item.case_name ??
    item.name ??
    `Case ${getCaseId(item) ?? ""}`.trim()
  );
}

function getCaseDate(item) {
  return (
    item.created_at ??
    item.createdAt ??
    item.capture_date ??
    item.image_capture_date ??
    item.updated_at
  );
}

function getCaseStatus(item) {
  return String(item.analysis_status ?? item.status ?? "pending").toLowerCase();
}

function getStatusStyle(status) {
  if (["completed", "complete", "success"].includes(status)) {
    return {
      label: "Completed",
      className: "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
      Icon: CheckCircle2,
    };
  }

  if (["failed", "error", "rejected"].includes(status)) {
    return {
      label: status === "rejected" ? "Rejected" : "Failed",
      className: "bg-red-50 text-red-700 ring-red-600/15",
      Icon: AlertCircle,
    };
  }

  if (
    ["processing", "in_progress", "in progress", "running"].includes(status)
  ) {
    return {
      label: "Processing",
      className: "bg-blue-50 text-blue-700 ring-blue-600/15",
      Icon: RefreshCw,
    };
  }

  return {
    label: "Pending",
    className: "bg-amber-50 text-amber-700 ring-amber-600/15",
    Icon: Clock3,
  };
}

function normalizeCases(data) {
  // Supports common API response shapes.
  // Adjust this if your backend returns a different schema.
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.cases)) return data.cases;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;
  if (Array.isArray(data?.data)) return data.data;

  return [];
}

export default function CasesPage() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  async function loadCases() {
    setLoading(true);
    setError("");

    try {
      const response = await getCases();
      setCases(normalizeCases(response));
    } catch (err) {
      setError(
        err.response?.status === 401
          ? "Your session may have expired. Please sign in again."
          : (err.response?.data?.detail ??
              "We couldn't load your cases. Please try again."),
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  const filteredCases = useMemo(() => {
    const query = search.trim().toLowerCase();

    return cases.filter((item) => {
      const id = String(getCaseId(item) ?? "");
      const title = getCaseTitle(item).toLowerCase();
      const status = getCaseStatus(item);

      const matchesSearch =
        !query || id.toLowerCase().includes(query) || title.includes(query);

      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "completed" &&
          ["completed", "complete", "success"].includes(status)) ||
        (statusFilter === "processing" &&
          ["processing", "in_progress", "in progress", "running"].includes(
            status,
          )) ||
        (statusFilter === "pending" &&
          ![
            "completed",
            "complete",
            "success",
            "processing",
            "in_progress",
            "in progress",
            "running",
            "failed",
            "error",
            "rejected",
          ].includes(status)) ||
        (statusFilter === "failed" &&
          ["failed", "error", "rejected"].includes(status));

      return matchesSearch && matchesStatus;
    });
  }, [cases, search, statusFilter]);

  const completedCount = cases.filter((item) =>
    ["completed", "complete", "success"].includes(getCaseStatus(item)),
  ).length;

  const pendingCount = cases.filter((item) =>
    ["pending", "queued"].includes(getCaseStatus(item)),
  ).length;

  return (
    <div className="flex h-screen overflow-hidden bg-[#F7F9FC]">
      <Sidebar role="user" />

      <main className="min-w-0 flex-1 overflow-y-auto">
        {/* Top bar */}
        <header
          className="sticky top-0 z-20 flex h-[72px]
          items-center justify-between border-b border-slate-200/80
          bg-white/90 px-5 backdrop-blur-md sm:px-8"
        >
          <div>
            <p className="text-sm font-semibold text-slate-800">My Cases</p>
            <p className="text-xs text-slate-500">
              Manage your skin analysis cases
            </p>
          </div>

          <Link
            to="/analysis/new"
            className="inline-flex items-center gap-2 rounded-xl
              bg-teal-700 px-4 py-2.5 text-sm font-semibold
              text-white shadow-sm transition hover:bg-teal-800"
          >
            <Plus size={17} />
            <span className="hidden sm:inline">New Case</span>
          </Link>
        </header>

        <div className="mx-auto max-w-[1440px] space-y-6 p-5 sm:p-8">
          {/* Page introduction */}
          <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <div
                className="mb-2 flex items-center gap-2 text-sm
                font-medium text-teal-700"
              >
                <FolderOpen size={17} />
                Your workspace
              </div>

              <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                Your cases
              </h1>

              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">
                View your cases, check analysis progress, and revisit previous
                results from one place.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <ShieldNote />
              Your personal case list
            </div>
          </section>

          {/* Summary cards */}
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <SummaryCard
              title="Total cases"
              value={loading ? "—" : cases.length}
              description="Cases in your account"
              icon={FolderOpen}
              iconClass="bg-teal-50 text-teal-700"
            />

            <SummaryCard
              title="Completed"
              value={loading ? "—" : completedCount}
              description="Cases marked as completed"
              icon={CheckCircle2}
              iconClass="bg-emerald-50 text-emerald-700"
            />

            <SummaryCard
              title="Pending"
              value={loading ? "—" : pendingCount}
              description="Cases awaiting analysis"
              icon={Clock3}
              iconClass="bg-amber-50 text-amber-700"
            />
          </section>

          {/* Case list */}
          <section
            className="overflow-hidden rounded-2xl border
            border-slate-200/80 bg-white shadow-sm shadow-slate-900/[0.02]"
          >
            <div
              className="flex flex-col gap-4 border-b
              border-slate-100 p-5 sm:flex-row sm:items-center
              sm:justify-between sm:px-6"
            >
              <div>
                <h2 className="font-bold text-slate-800">All cases</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {loading
                    ? "Loading your cases..."
                    : `${filteredCases.length} ${
                        filteredCases.length === 1 ? "case" : "cases"
                      } found`}
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <div className="relative">
                  <Search
                    size={17}
                    className="absolute left-3 top-1/2
                      -translate-y-1/2 text-slate-400"
                  />
                  <input
                    type="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search cases..."
                    aria-label="Search cases"
                    className="h-10 w-full rounded-xl border
                      border-slate-200 bg-slate-50 pl-9 pr-3
                      text-sm text-slate-700 outline-none
                      transition placeholder:text-slate-400
                      focus:border-teal-400 focus:bg-white
                      focus:ring-4 focus:ring-teal-500/10
                      sm:w-56"
                  />
                </div>

                <div className="relative">
                  <SlidersHorizontal
                    size={15}
                    className="pointer-events-none absolute left-3
                      top-1/2 -translate-y-1/2 text-slate-400"
                  />
                  <select
                    value={statusFilter}
                    onChange={(event) => setStatusFilter(event.target.value)}
                    aria-label="Filter cases by status"
                    className="h-10 w-full appearance-none rounded-xl
                      border border-slate-200 bg-white pl-9 pr-8
                      text-sm text-slate-700 outline-none
                      focus:border-teal-400 focus:ring-4
                      focus:ring-teal-500/10 sm:w-40"
                  >
                    <option value="all">All statuses</option>
                    <option value="completed">Completed</option>
                    <option value="processing">Processing</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
              </div>
            </div>

            {error && (
              <div
                className="m-5 flex flex-col gap-3 rounded-xl
                border border-red-200 bg-red-50 p-4 sm:flex-row
                sm:items-center sm:justify-between"
              >
                <div className="flex items-start gap-3">
                  <AlertCircle
                    size={19}
                    className="mt-0.5 shrink-0 text-red-600"
                  />
                  <div>
                    <p className="text-sm font-semibold text-red-800">
                      Unable to load cases
                    </p>
                    <p className="mt-1 text-sm text-red-700">{error}</p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={loadCases}
                  className="inline-flex items-center justify-center gap-2
                    rounded-lg border border-red-200 bg-white
                    px-3 py-2 text-sm font-semibold text-red-700
                    hover:bg-red-100"
                >
                  <RefreshCw size={15} />
                  Retry
                </button>
              </div>
            )}

            {loading ? (
              <div className="space-y-4 p-6">
                {[1, 2, 3, 4].map((item) => (
                  <div key={item} className="flex animate-pulse gap-4">
                    <div className="h-11 w-11 rounded-xl bg-slate-100" />
                    <div className="flex-1 space-y-2 py-1">
                      <div className="h-3 w-1/3 rounded bg-slate-100" />
                      <div className="h-3 w-1/2 rounded bg-slate-100" />
                    </div>
                    <div className="h-6 w-20 rounded-full bg-slate-100" />
                  </div>
                ))}
              </div>
            ) : !error && filteredCases.length === 0 ? (
              <div className="flex flex-col items-center px-5 py-14 text-center">
                <div
                  className="flex h-16 w-16 items-center
                  justify-center rounded-2xl bg-teal-50 text-teal-700"
                >
                  <FolderOpen size={28} strokeWidth={1.7} />
                </div>

                <h3 className="mt-5 font-semibold text-slate-800">
                  {cases.length === 0 ? "No cases yet" : "No matching cases"}
                </h3>

                <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                  {cases.length === 0
                    ? "Create a case to start organizing your skin images and future analysis results."
                    : "Try a different search term or change the status filter."}
                </p>

                {cases.length === 0 ? (
                  <Link
                    to="/analysis/new"
                    className="mt-5 inline-flex items-center gap-2
                      rounded-xl bg-teal-700 px-4 py-2.5
                      text-sm font-semibold text-white
                      transition hover:bg-teal-800"
                  >
                    <Plus size={17} />
                    Create your first case
                  </Link>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setSearch("");
                      setStatusFilter("all");
                    }}
                    className="mt-5 text-sm font-semibold text-teal-700
                      hover:text-teal-900"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[650px] text-left">
                  <thead className="bg-slate-50/80">
                    <tr
                      className="text-[11px] font-semibold
                      uppercase tracking-wider text-slate-500"
                    >
                      <th className="px-6 py-4">Case</th>
                      <th className="px-5 py-4">Created</th>
                      <th className="px-5 py-4">Status</th>
                      <th className="px-6 py-4 text-right">Action</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-100">
                    {filteredCases.map((item, index) => {
                      const id = getCaseId(item);
                      const status = getStatusStyle(getCaseStatus(item));
                      const StatusIcon = status.Icon;
                      const title = getCaseTitle(item);

                      return (
                        <tr
                          key={id ?? index}
                          className="transition hover:bg-slate-50/80"
                        >
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div
                                className="flex h-11 w-11 shrink-0
                                items-center justify-center rounded-xl
                                border border-teal-100 bg-teal-50
                                text-teal-700"
                              >
                                <FileText size={19} />
                              </div>

                              <div>
                                <p className="text-sm font-semibold text-slate-800">
                                  {title}
                                </p>
                                <p className="mt-1 text-xs text-slate-500">
                                  {id != null
                                    ? `ID: ${id}`
                                    : "Case ID unavailable"}
                                </p>
                              </div>
                            </div>
                          </td>

                          <td className="px-5 py-4">
                            <div
                              className="flex items-center gap-2
                              text-sm text-slate-600"
                            >
                              <CalendarDays
                                size={15}
                                className="text-slate-400"
                              />
                              {formatDate(getCaseDate(item))}
                            </div>
                          </td>

                          <td className="px-5 py-4">
                            <span
                              className={`inline-flex items-center
                              gap-1.5 rounded-full px-2.5 py-1
                              text-xs font-semibold ring-1 ring-inset
                              ${status.className}`}
                            >
                              <StatusIcon size={13} />
                              {status.label}
                            </span>
                          </td>

                          <td className="px-6 py-4 text-right">
                            {id != null ? (
                              <Link
                                to={`/cases/${encodeURIComponent(id)}`}
                                className="inline-flex items-center gap-1.5
                                  rounded-lg px-3 py-2 text-sm
                                  font-semibold text-teal-700
                                  transition hover:bg-teal-50"
                              >
                                View case
                                <ArrowRight size={15} />
                              </Link>
                            ) : (
                              <span className="text-xs text-slate-400">
                                No case ID
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <p className="text-center text-xs leading-5 text-slate-400">
            DermAI provides AI-assisted analysis and is not a standalone medical
            diagnosis.
          </p>
        </div>
      </main>
    </div>
  );
}

function SummaryCard({ title, value, description, icon: Icon, iconClass }) {
  return (
    <article
      className="rounded-2xl border border-slate-200/80
      bg-white p-5 shadow-sm shadow-slate-900/[0.02]"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-800">
            {value}
          </p>
        </div>

        <div className={`rounded-xl p-3 ${iconClass}`}>
          <Icon size={21} />
        </div>
      </div>

      <p className="mt-4 text-xs text-slate-500">{description}</p>
    </article>
  );
}

function ShieldNote() {
  return (
    <span className="inline-flex items-center gap-1.5">
      <Activity size={15} />
      Personal workspace
    </span>
  );
}
