/** @format */

import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  ArrowLeftToLine,
  ArrowRightToLine,
  Bell,
  CircleHelp,
  ClipboardList,
  FileText,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Microscope,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  UserRound,
} from "lucide-react";

import { navigationByRole } from "./navigation";

const iconByLabel = {
  Dashboard: LayoutDashboard,
  Patients: Users,
  Cases: ClipboardList,
  "Cases & Analyses": ClipboardList,
  "New Analysis": Sparkles,
  "My Cases": ClipboardList,
  "Prediction History": Activity,
  "My Reports": FileText,
  Reports: FileText,
  "Model Insights": Microscope,
  Experiments: FlaskConical,
  "Model Performance": Activity,
  Users,
  "Model Usage": Activity,
  "System Activity": Bell,
  "Platform Health": ShieldCheck,
  Settings,
  Profile: UserRound,
};

export default function Sidebar({
  role = "user",
  user = { name: "DermAI User", email: "user@dermai.com" },
  onLogout,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const navigation = navigationByRole[role] ?? navigationByRole.user;

  return (
    <aside
      className={`relative flex h-screen shrink-0 flex-col
        border-r border-slate-200 bg-white
        transition-[width] duration-300 ease-in-out
        ${collapsed ? "w-[82px]" : "w-[260px]"}`}
    >
      {/* Brand */}
      <div
        className={`flex h-[82px] shrink-0 items-center
          border-b border-slate-100
          ${collapsed ? "justify-center px-3" : "gap-3 px-5"}`}
      >
        <div
          className="flex h-11 w-11 shrink-0 items-center
          justify-center rounded-2xl bg-teal-50 text-teal-600
          ring-1 ring-teal-100"
        >
          <Activity size={24} strokeWidth={2.2} />
        </div>

        {!collapsed && (
          <div className="min-w-0">
            <h1 className="text-xl font-bold tracking-tight text-slate-800">
              Derm<span className="text-teal-600">AI</span>
            </h1>
            <p className="mt-0.5 text-[11px] text-slate-500">
              Skin Analysis Platform
            </p>
          </div>
        )}
      </div>

      {/* Collapse control */}
      <button
        type="button"
        onClick={() => setCollapsed((value) => !value)}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        className="absolute -right-3 top-[94px] z-10
          flex h-6 w-6 items-center justify-center
          rounded-full border border-slate-200 bg-white
          text-slate-500 shadow-sm transition
          hover:border-teal-300 hover:text-teal-700"
      >
        {collapsed ? (
          <ArrowRightToLine size={13} />
        ) : (
          <ArrowLeftToLine size={13} />
        )}
      </button>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-6">
        {!collapsed && (
          <p
            className="mb-3 px-3 text-[10px] font-semibold
            uppercase tracking-[0.16em] text-slate-400"
          >
            Workspace
          </p>
        )}

        <nav className="space-y-1" aria-label="Main navigation">
          {navigation.map((item) => {
            const Icon = iconByLabel[item.label] ?? Activity;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `group relative flex items-center gap-3
                  rounded-xl px-3 py-3 text-[13px] font-medium
                  transition-all duration-200
                  ${
                    isActive
                      ? "bg-teal-50 text-teal-700"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }
                  ${collapsed ? "justify-center" : ""}`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <span
                        className="absolute bottom-2 left-0
                        top-2 w-[3px] rounded-r-full bg-teal-600"
                      />
                    )}

                    <Icon
                      size={19}
                      strokeWidth={isActive ? 2.2 : 1.8}
                      className={`shrink-0 transition-colors ${
                        isActive
                          ? "text-teal-700"
                          : "text-slate-400 group-hover:text-slate-700"
                      }`}
                    />

                    {!collapsed && (
                      <>
                        <span className="flex-1 truncate">{item.label}</span>

                        {item.badge && (
                          <span
                            className="rounded-full bg-teal-100
                            px-2 py-0.5 text-[10px] font-semibold
                            text-teal-700"
                          >
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Support */}
        <div className="my-5 border-t border-slate-100" />

        {!collapsed && (
          <p
            className="mb-3 px-3 text-[10px] font-semibold
            uppercase tracking-[0.16em] text-slate-400"
          >
            Support
          </p>
        )}

        <a
          href="/help"
          title={collapsed ? "Help & Support" : undefined}
          className={`flex items-center gap-3 rounded-xl px-3 py-3
            text-[13px] font-medium text-slate-600 transition
            hover:bg-slate-50 hover:text-slate-900
            ${collapsed ? "justify-center" : ""}`}
        >
          <CircleHelp size={19} className="shrink-0 text-slate-400" />
          {!collapsed && <span>Help & Support</span>}
        </a>

        <a
          href="/settings"
          title={collapsed ? "Settings" : undefined}
          className={`flex items-center gap-3 rounded-xl px-3 py-3
            text-[13px] font-medium text-slate-600 transition
            hover:bg-slate-50 hover:text-slate-900
            ${collapsed ? "justify-center" : ""}`}
        >
          <Settings size={19} className="shrink-0 text-slate-400" />
          {!collapsed && <span>Preferences</span>}
        </a>
      </div>

      {/* User profile */}
      <div className="shrink-0 border-t border-slate-100 p-3">
        <div
          className={`flex items-center gap-3 rounded-xl p-2
            transition hover:bg-slate-50
            ${collapsed ? "justify-center" : ""}`}
        >
          <div
            className="flex h-10 w-10 shrink-0 items-center
            justify-center rounded-xl bg-gradient-to-br
            from-teal-100 to-cyan-50 text-sm font-bold
            text-teal-700 ring-1 ring-teal-100"
          >
            {(user.name || "User")
              .split(" ")
              .map((part) => part[0])
              .join("")
              .slice(0, 2)
              .toUpperCase()}
          </div>

          {!collapsed && (
            <>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-semibold text-slate-800">
                  {user.name}
                </p>
                <p className="truncate text-[11px] capitalize text-slate-500">
                  {role.replaceAll("_", " ")}
                </p>
              </div>

              <button
                type="button"
                onClick={onLogout}
                title="Log out"
                className="rounded-lg p-2 text-slate-400
                  transition hover:bg-red-50 hover:text-red-600"
              >
                <LogOut size={17} />
              </button>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
