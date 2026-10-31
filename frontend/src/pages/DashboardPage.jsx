import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowRight, ClipboardList, FileClock, FolderOpen, Plus, ShieldCheck, Users } from "lucide-react";
import { useAuth } from "../state/AuthContext";
import { adminApi, caseApi, patientApi } from "../api/services";
import { errorMessage } from "../api/client";
import { Button, EmptyState, Metric, Notice, PageTitle, SectionHeading } from "../components/ui";

const roleInfo = {
  user: { title: "Your care workspace", description: "A clear, private place to keep your case records and skin images together." },
  clinician: { title: "Clinical workspace", description: "Manage patient records, review case context, and organize image intake." },
  researcher: { title: "Research workspace", description: "Your account is active. Research datasets and analytics are not connected to this backend." },
  data_scientist: { title: "Model workspace", description: "Your account is active. Model registry and evaluation data are not connected to this backend." },
  admin: { title: "Platform overview", description: "Manage access and review recorded system activity." },
};
const dateLabel = (value) => value ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value)) : "Date unavailable";

export default function DashboardPage() {
  const { user } = useAuth();
  const role = user?.role || "user";
  const [cases, setCases] = useState([]);
  const [patients, setPatients] = useState([]);
  const [adminData, setAdminData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        if (["user", "clinician"].includes(role)) {
          const results = await Promise.all([caseApi.list({ limit: 6 }), role === "clinician" ? patientApi.list({ limit: 100 }) : Promise.resolve([])]);
          if (active) { setCases(results[0]); setPatients(results[1]); }
        } else if (role === "admin") {
          const results = await Promise.all([adminApi.users(), adminApi.audit({ limit: 6 })]);
          if (active) setAdminData({ users: results[0], audit: results[1] });
        }
      } catch (err) { if (active) setError(errorMessage(err, "Some overview information could not be loaded.")); }
      finally { if (active) setLoading(false); }
    }
    load(); return () => { active = false; };
  }, [role]);

  const recentWithImage = cases.filter((item) => item.status === "image_uploaded").length;
  const patientName = role === "user" ? user?.username : null;
  return <div className="space-y-8">
    <PageTitle eyebrow={roleInfo[role]?.title} title={patientName ? `Good to see you, ${patientName}` : `Welcome${user?.username ? `, ${user.username}` : ""}`} description={roleInfo[role]?.description} action={(["user", "clinician"].includes(role)) && <Button as={Link} to={role === "clinician" ? "/app/patients" : "/app/upload"}><Plus size={16}/>{role === "clinician" ? "Add patient" : "Add an image"}</Button>}/>
    {error && <Notice kind="error">{error}</Notice>}

    {(["user", "clinician"].includes(role)) && <>
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"><Metric label="Cases on this page" value={loading ? "—" : cases.length} detail="Most recent records" icon={FolderOpen}/>{role === "clinician" ? <Metric label="Patient records" value={loading ? "—" : patients.length} detail="First 100 accessible records" icon={Users}/> : <Metric label="Images received" value={loading ? "—" : recentWithImage} detail="Cases with an uploaded image" icon={Activity}/>}<Metric label="Analysis results" value="Not available" detail="The backend does not provide predictions" icon={FileClock}/></section>
      <section className="rounded-2xl border border-[#e4e1da] bg-white p-5 sm:p-6"><SectionHeading title="Recent cases" description="Latest records from your account" action={<Link to="/app/cases" className="inline-flex items-center gap-1 text-sm font-semibold text-[#a25539] hover:underline">View all <ArrowRight size={15}/></Link>}/>
        {loading ? <div role="status" className="py-12 text-center text-sm text-[#7a776f]">Loading your workspace…</div> : cases.length === 0 ? <EmptyState title="Your case list is ready" description="Create a case to begin organizing image records. Your first case will appear here." icon={FolderOpen} action={<Button as={Link} to="/app/cases/new"><Plus size={15}/>Create a case</Button>}/> : <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[620px] text-left"><thead className="border-y border-[#eeece6] bg-[#fbfaf8] text-[10px] uppercase tracking-[0.14em] text-[#89867e]"><tr><th className="px-4 py-3 font-semibold">Case</th><th className="px-4 py-3 font-semibold">Location</th><th className="px-4 py-3 font-semibold">Status</th><th className="px-4 py-3 font-semibold">Created</th><th className="px-4 py-3"/></tr></thead><tbody className="divide-y divide-[#efede8]">{cases.map((item) => <tr key={item.id} className="hover:bg-[#fcfbf9]"><td className="px-4 py-3.5"><Link to={`/app/cases/${item.id}`} className="text-sm font-semibold text-[#383731] hover:text-[#a25539]">{item.case_label || "Untitled case"}</Link><p className="mt-1 font-mono text-[10px] text-[#929087]">{item.id}</p></td><td className="px-4 py-3.5 text-sm text-[#6e6b63]">{item.body_location || "Not recorded"}</td><td className="px-4 py-3.5"><span className="rounded-full bg-[#f1eee8] px-2.5 py-1 text-xs capitalize text-[#625e55]">{item.status?.replaceAll("_", " ") || "Unknown"}</span></td><td className="px-4 py-3.5 text-sm text-[#77746c]">{dateLabel(item.created_at)}</td><td className="px-4 py-3.5 text-right"><Link to={`/app/cases/${item.id}`} aria-label="Open case" className="inline-flex rounded-md p-2 text-[#807c73] hover:bg-[#f1eee8]"><ArrowRight size={15}/></Link></td></tr>)}</tbody></table></div>}
      </section>
      <Notice kind="info">DermAI currently supports case and patient records, image uploads, and image preprocessing previews. It does not produce a diagnosis or prediction.</Notice>
    </>}

    {role === "admin" && <><section className="grid gap-3 sm:grid-cols-2"><Metric label="Accounts returned" value={loading ? "—" : adminData?.users.length ?? "—"} detail="Up to 100 most recent accounts" icon={Users}/><Metric label="Recent audit events" value={loading ? "—" : adminData?.audit.length ?? "—"} detail="Latest 6 recorded events" icon={ShieldCheck}/></section><div className="grid gap-4 lg:grid-cols-2">{[{ title: "Account access", to: "/app/admin/users", icon: Users, body: "Review user roles and active status. Role updates revoke existing sessions." }, { title: "Audit trail", to: "/app/admin/audit", icon: ShieldCheck, body: "Inspect the access and workflow events available from the audit API." }].map(({ title, to, icon: Icon, body }) => <Link key={to} to={to} className="group rounded-2xl border border-[#e4e1da] bg-white p-5 transition hover:border-[#d5b6a5]"><Icon size={18} className="text-[#a25539]"/><h2 className="mt-4 font-semibold">{title}</h2><p className="mt-1 text-sm leading-6 text-[#77746c]">{body}</p><span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[#a25539]">Open workspace <ArrowRight size={15} className="transition group-hover:translate-x-1"/></span></Link>)}</div></>}

    {["researcher", "data_scientist"].includes(role) && <section className="rounded-2xl border border-[#e4e1da] bg-white p-6 sm:p-8"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f2efe8] text-[#8b6a58]"><ClipboardList size={19}/></span><h2 className="display-serif mt-4 text-2xl">This workspace is not connected yet</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-[#716e66]">{role === "researcher" ? "The current backend has no research dataset, case cohort analytics, or export endpoints." : "The current backend has no model registry, training history, evaluation metrics, or inference monitoring endpoints."} This dashboard will show those modules when the backend provides them; no sample values are shown.</p><p className="mt-5 text-xs text-[#908c83]">Available modules for your role may be enabled by future backend releases.</p></section>}
  </div>;
}
