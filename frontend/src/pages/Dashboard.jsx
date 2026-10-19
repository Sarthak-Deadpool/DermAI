/** @format */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  Bell,
  CalendarDays,
  ClipboardList,
  Clock3,
  FileText,
  ImagePlus,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";

import Sidebar from "../components/sidebar/Sidebar";
import authServices from "../services/authService";

const overviewCards = [
  {
    title: "Total analyses",
    value: "—",
    description: "Your completed skin analyses",
    icon: Activity,
    color: "bg-teal-50 text-teal-700",
  },
  {
    title: "Recent analyses",
    value: "—",
    description: "Your latest analysis activity",
    icon: Clock3,
    color: "bg-blue-50 text-blue-700",
  },
  {
    title: "Available reports",
    value: "—",
    description: "Reports ready to view",
    icon: FileText,
    color: "bg-violet-50 text-violet-700",
  },
];

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [userError, setUserError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadUser() {
      try {
        const data = await authServices.getCurrentUser();

        if (mounted) {
          // Adjust this mapping to match your actual /auth/me response.
          setUser(data.user ?? data);
        }
      } catch (error) {
        if (mounted) {
          setUserError(
            error.response?.status === 401
              ? "Your session may have expired. Please sign in again."
              : "We couldn't load your profile. Please try again.",
          );
        }
      } finally {
        if (mounted) setLoadingUser(false);
      }
    }

    loadUser();

    return () => {
      mounted = false;
    };
  }, []);

  const displayName =
    user?.full_name ?? user?.name ?? user?.username ?? "there";

  const sidebarUser = {
    name: displayName === "there" ? "DermAI User" : displayName,
    email: user?.email ?? "",
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#F7F9FC]">
      <Sidebar role="user" user={sidebarUser} />

      <main className="min-w-0 flex-1 overflow-y-auto">
        {/* Top bar */}
        <header
          className="sticky top-0 z-20 flex h-[72px]
          items-center justify-between border-b border-slate-200/80
          bg-white/90 px-5 backdrop-blur-md sm:px-8"
        >
          <div className="flex min-w-0 items-center gap-3">
            <div
              className="hidden h-10 w-10 items-center
              justify-center rounded-xl bg-slate-100 text-slate-500 sm:flex"
            >
              <Search size={19} />
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-800">
                My Dashboard
              </p>
              <p className="text-xs text-slate-500">
                Your personal analysis workspace
              </p>
            </div>
          </div>

          <button
            type="button"
            aria-label="Notifications"
            className="relative rounded-xl border border-slate-200
              bg-white p-2.5 text-slate-500 transition
              hover:bg-slate-50 hover:text-teal-700"
          >
            <Bell size={19} />
          </button>
        </header>

        <div className="mx-auto max-w-[1440px] space-y-7 p-5 sm:p-8">
          {/* Welcome banner */}
          <section
            className="relative overflow-hidden rounded-3xl
            bg-gradient-to-r from-teal-700 via-teal-600 to-cyan-600
            px-6 py-7 text-white shadow-lg shadow-teal-900/10 sm:px-9 sm:py-9"
          >
            <div
              className="pointer-events-none absolute -right-12
              -top-24 h-72 w-72 rounded-full border
              border-white/10 sm:right-12"
            />
            <div
              className="pointer-events-none absolute -right-4
              -top-12 h-52 w-52 rounded-full border border-white/10"
            />

            <div className="relative z-10 max-w-2xl">
              <div
                className="mb-4 inline-flex items-center gap-2
                rounded-full border border-white/20 bg-white/10
                px-3 py-1.5 text-xs font-medium text-teal-50"
              >
                <Sparkles size={14} />
                Your personal health workspace
              </div>

              <h1
                className="text-2xl font-bold tracking-tight
                sm:text-3xl"
              >
                {loadingUser ? "Welcome to DermAI" : `Welcome, ${displayName}`}
              </h1>

              <p className="mt-3 max-w-xl text-sm leading-6 text-teal-50/90">
                Review your previous skin image analyses, revisit predictions,
                and access your reports in one place.
              </p>

              <Link
                to="/cases/new"
                className="mt-6 inline-flex items-center gap-2 rounded-xl
  bg-white px-5 py-3 text-sm font-semibold text-teal-800
  shadow-sm transition hover:-translate-y-0.5 hover:bg-teal-50"
              >
                <ImagePlus size={18} />
                Create new case
                <ArrowRight size={16} />
              </Link>
            </div>
          </section>

          {userError && (
            <div
              role="alert"
              className="flex items-start gap-3
              rounded-xl border border-amber-200 bg-amber-50
              p-4 text-sm text-amber-800"
            >
              <ShieldCheck size={19} className="mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold">Profile unavailable</p>
                <p className="mt-1">{userError}</p>
              </div>
            </div>
          )}

          {/* Overview */}
          <section>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-800">
                  Your overview
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  A summary of your DermAI activity
                </p>
              </div>

              <CalendarDays size={19} className="text-slate-400" />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {overviewCards.map((card) => {
                const Icon = card.icon;

                return (
                  <article
                    key={card.title}
                    className="rounded-2xl border border-slate-200/80
                      bg-white p-5 shadow-sm shadow-slate-900/[0.02]
                      transition hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-500">
                          {card.title}
                        </p>
                        <p
                          className="mt-3 text-3xl font-bold
                          tracking-tight text-slate-800"
                        >
                          {card.value}
                        </p>
                      </div>

                      <div className={`rounded-xl p-3 ${card.color}`}>
                        <Icon size={21} />
                      </div>
                    </div>

                    <p className="mt-4 text-xs text-slate-500">
                      {card.description}
                    </p>
                  </article>
                );
              })}
            </div>
          </section>

          {/* Recent analyses */}
          <section
            className="overflow-hidden rounded-2xl
            border border-slate-200/80 bg-white shadow-sm
            shadow-slate-900/[0.02]"
          >
            <div
              className="flex flex-wrap items-center
              justify-between gap-3 border-b border-slate-100
              px-5 py-5 sm:px-6"
            >
              <div>
                <h2 className="font-bold text-slate-800">Recent analyses</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Your latest image analysis results
                </p>
              </div>

              <Link
                to="/history"
                className="inline-flex items-center gap-1.5
                  text-sm font-semibold text-teal-700
                  hover:text-teal-900"
              >
                View history
                <ArrowRight size={16} />
              </Link>
            </div>

            {/* Empty state until analysis API is connected */}
            <div className="flex flex-col items-center px-5 py-12 text-center">
              <div
                className="flex h-16 w-16 items-center
                justify-center rounded-2xl bg-teal-50 text-teal-700"
              >
                <Upload size={27} strokeWidth={1.7} />
              </div>

              <h3 className="mt-5 font-semibold text-slate-800">
                No analyses to display yet
              </h3>

              <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                When you analyze a skin image, its result, confidence score, and
                analysis date can appear here.
              </p>

              <Link
                to="/analysis/new"
                className="mt-5 inline-flex items-center gap-2
                  rounded-xl border border-teal-200 bg-white
                  px-4 py-2.5 text-sm font-semibold text-teal-700
                  transition hover:bg-teal-50"
              >
                <ImagePlus size={17} />
                Create your first analysis
              </Link>
            </div>
          </section>

          {/* Quick access */}
          <section>
            <div className="mb-4">
              <h2 className="text-lg font-bold text-slate-800">Quick access</h2>
              <p className="mt-1 text-sm text-slate-500">
                Continue where you left off
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Link
                to="/history"
                className="group flex items-center gap-4 rounded-2xl
                  border border-slate-200/80 bg-white p-5 shadow-sm
                  transition hover:border-teal-200 hover:shadow-md"
              >
                <div
                  className="flex h-12 w-12 shrink-0 items-center
                  justify-center rounded-xl bg-blue-50 text-blue-700"
                >
                  <ClipboardList size={22} />
                </div>

                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-slate-800">
                    Prediction history
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Review previous predictions and analyses.
                  </p>
                </div>

                <ArrowRight
                  size={18}
                  className="text-slate-400
                  transition group-hover:translate-x-1
                  group-hover:text-teal-700"
                />
              </Link>

              <Link
                to="/reports"
                className="group flex items-center gap-4 rounded-2xl
                  border border-slate-200/80 bg-white p-5 shadow-sm
                  transition hover:border-teal-200 hover:shadow-md"
              >
                <div
                  className="flex h-12 w-12 shrink-0 items-center
                  justify-center rounded-xl bg-violet-50 text-violet-700"
                >
                  <FileText size={22} />
                </div>

                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-slate-800">My reports</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Access your available analysis reports.
                  </p>
                </div>

                <ArrowRight
                  size={18}
                  className="text-slate-400
                  transition group-hover:translate-x-1
                  group-hover:text-teal-700"
                />
              </Link>
            </div>
          </section>

          {/* Medical disclaimer */}
          <footer
            className="flex items-start gap-3 rounded-2xl
            border border-amber-200/80 bg-amber-50/70 p-4 sm:p-5"
          >
            <ShieldCheck
              size={20}
              className="mt-0.5 shrink-0
              text-amber-700"
            />

            <div>
              <h3 className="text-sm font-semibold text-amber-900">
                Important health information
              </h3>
              <p className="mt-1 text-xs leading-5 text-amber-800">
                DermAI provides AI-assisted skin image analysis for preliminary
                screening and decision support. Predictions and confidence
                scores are not a standalone medical diagnosis. Consult a
                qualified healthcare professional about medical concerns.
              </p>
            </div>
          </footer>
        </div>
      </main>
    </div>
  );
}
