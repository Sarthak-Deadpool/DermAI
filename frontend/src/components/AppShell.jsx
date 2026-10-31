import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Activity, ChevronLeft, ChevronRight, CircleUserRound, ClipboardList, LayoutDashboard, LogOut, Menu, Settings2, Shield, Users, X } from "lucide-react";
import { useAuth } from "../state/AuthContext";

const linksByRole = {
  user: [{ label: "Overview", to: "/app", icon: LayoutDashboard }, { label: "My cases", to: "/app/cases", icon: ClipboardList }, { label: "Image intake", to: "/app/upload", icon: Activity }, { label: "My profile", to: "/app/profile", icon: CircleUserRound }],
  clinician: [{ label: "Overview", to: "/app", icon: LayoutDashboard }, { label: "Patients", to: "/app/patients", icon: Users }, { label: "Case management", to: "/app/cases", icon: ClipboardList }, { label: "Image intake", to: "/app/upload", icon: Activity }, { label: "Account & sessions", to: "/app/profile", icon: Settings2 }],
  researcher: [{ label: "Overview", to: "/app", icon: LayoutDashboard }, { label: "Account & sessions", to: "/app/profile", icon: Settings2 }],
  data_scientist: [{ label: "Overview", to: "/app", icon: LayoutDashboard }, { label: "Account & sessions", to: "/app/profile", icon: Settings2 }],
  admin: [{ label: "Overview", to: "/app", icon: LayoutDashboard }, { label: "Users & roles", to: "/app/admin/users", icon: Users }, { label: "Audit log", to: "/app/admin/audit", icon: Shield }, { label: "Account & sessions", to: "/app/profile", icon: Settings2 }],
};
const roleLabel = { user: "Patient workspace", clinician: "Clinical workspace", researcher: "Research workspace", data_scientist: "Model workspace", admin: "Administration" };

function SidebarContent({ collapsed, closeMobile }) {
  const { user, logout } = useAuth();
  const items = linksByRole[user?.role] || linksByRole.user;
  return <>
    <div className={`flex h-[76px] shrink-0 items-center border-b border-[#e8e5de] ${collapsed ? "justify-center px-2" : "gap-3 px-5"}`}><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#e9ded4] text-[#98563c]"><Activity size={18}/></span>{!collapsed && <div><p className="display-serif text-[22px] leading-none text-[#302e29]">DermAI</p><p className="mt-1 text-[10px] font-medium uppercase tracking-[0.14em] text-[#88847b]">Care workspace</p></div>}</div>
    {!collapsed && <p className="px-5 pb-2 pt-6 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#9a968c]">{roleLabel[user?.role] || "Workspace"}</p>}
    <nav aria-label="Primary navigation" className="flex-1 space-y-1 overflow-y-auto px-3 py-2">{items.map(({ label, to, icon: Icon }) => <NavLink key={to} to={to} end={to === "/app"} onClick={closeMobile} title={collapsed ? label : undefined} className={({ isActive }) => `flex min-h-10 items-center gap-3 rounded-lg px-3 text-[13px] transition ${isActive ? "bg-[#eee8df] font-semibold text-[#6f3c29]" : "text-[#605e57] hover:bg-[#f0eee8] hover:text-[#302e29]"} ${collapsed ? "justify-center" : ""}`}><Icon size={17} strokeWidth={1.8}/>{!collapsed && <span>{label}</span>}{!collapsed && <span className="ml-auto"/>}</NavLink>)}</nav>
    <div className="border-t border-[#e8e5de] p-3"><div className={`flex items-center gap-3 rounded-lg p-2 ${collapsed ? "justify-center" : ""}`}><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#e7e4dc] text-xs font-semibold uppercase text-[#5d5a53]">{(user?.username || user?.email || "U").slice(0, 2)}</span>{!collapsed && <><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold text-[#393832]">{user?.username || user?.email}</p><p className="truncate text-[11px] capitalize text-[#89867e]">{user?.role?.replaceAll("_", " ")}</p></div><button type="button" onClick={logout} title="Sign out" className="rounded-md p-2 text-[#77746c] hover:bg-white hover:text-[#a25338]"><LogOut size={16}/></button></>}</div></div>
  </>;
}

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();
  return <div className="min-h-screen bg-[#f7f5f0] text-[#292823]">
    <aside className={`fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-[#e8e5de] bg-[#faf9f6] transition-[width] md:flex ${collapsed ? "w-[76px]" : "w-[252px]"}`}><SidebarContent collapsed={collapsed}/><button type="button" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-[#e2dfd8] bg-[#faf9f6] text-[#77746c] shadow-sm hover:text-[#9a553b]">{collapsed ? <ChevronRight size={14}/> : <ChevronLeft size={14}/>}</button></aside>
    {mobileOpen && <div className="fixed inset-0 z-50 md:hidden"><button type="button" onClick={() => setMobileOpen(false)} aria-label="Close menu" className="absolute inset-0 bg-black/30"/><aside className="absolute inset-y-0 left-0 flex w-[min(82vw,300px)] flex-col border-r border-[#e8e5de] bg-[#faf9f6] shadow-xl"><div className="flex justify-end p-3"><button type="button" aria-label="Close menu" onClick={() => setMobileOpen(false)}><X size={20}/></button></div><SidebarContent collapsed={false} closeMobile={() => setMobileOpen(false)}/></aside></div>}
    <div className={`min-h-screen transition-[padding] ${collapsed ? "md:pl-[76px]" : "md:pl-[252px]"}`}>
      <header className="sticky top-0 z-20 flex h-[62px] items-center justify-between border-b border-[#e8e5de] bg-[#f7f5f0]/95 px-4 backdrop-blur sm:px-7"><div className="flex items-center gap-3"><button type="button" onClick={() => setMobileOpen(true)} aria-label="Open navigation" className="rounded-lg p-2 hover:bg-[#efede7] md:hidden"><Menu size={19}/></button><div className="hidden items-center gap-2 text-xs text-[#8b887f] sm:flex"><span>DermAI</span><span>/</span><span className="capitalize text-[#4c4a44]">{location.pathname.split("/").filter(Boolean).at(-1)?.replaceAll("-", " ") || "Overview"}</span></div></div><div className="flex items-center gap-2 text-sm text-[#5e5b54]"><span className="hidden capitalize sm:block">{user?.role?.replaceAll("_", " ")}</span><span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#e7e4dc] text-[11px] font-semibold uppercase">{(user?.username || user?.email || "U").slice(0, 2)}</span></div></header>
      <main className="mx-auto max-w-[1500px] px-4 py-7 sm:px-7 lg:px-10"><Outlet/></main>
    </div>
  </div>;
}
