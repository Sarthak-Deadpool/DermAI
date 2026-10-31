import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowRight, CalendarDays, ClipboardList, ImagePlus, Plus, Search } from "lucide-react";
import { caseApi, patientApi } from "../api/services";
import { errorMessage } from "../api/client";
import { useAuth } from "../state/AuthContext";
import { Button, EmptyState, Loading, Notice, PageTitle, SearchField, SelectField } from "../components/ui";

const dateLabel = (value) => value ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value)) : "—";

export default function CasesPage() {
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const result = await caseApi.list({ offset, limit: 20, ...(status ? { status } : {}) });
      setCases(result); setHasNext(result.length === 20);
    } catch (err) { setError(errorMessage(err, "Could not load cases.")); }
    finally { setLoading(false); }
  }
  useEffect(() => {
    let active = true;
    caseApi.list({ offset, limit: 20, ...(status ? { status } : {}) }).then((result) => { if (active) { setCases(result); setHasNext(result.length === 20); } }).catch((err) => { if (active) setError(errorMessage(err, "Could not load cases.")); }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [offset, status]);
  useEffect(() => {
    if (user?.role !== "clinician") return;
    let active = true;
    patientApi.list({ limit: 100 }).then((result) => { if (active) setPatients(result); }).catch(() => {});
    return () => { active = false; };
  }, [user?.role]);
  const patientNames = useMemo(() => Object.fromEntries(patients.map((patient) => [patient.id, patient.patient_name || patient.patient_code])), [patients]);
  const filtered = cases.filter((item) => `${item.case_label || ""} ${item.id} ${item.body_location || ""} ${patientNames[item.patient_id] || ""}`.toLowerCase().includes(search.toLowerCase()));

  return <div className="space-y-7">
    <PageTitle eyebrow="Case records" title="Case management" description="Search, review, and organize case records. Image intake is available; prediction and diagnosis results are not provided by this backend." action={<Button as={Link} to="/app/cases/new"><Plus size={16}/>New case</Button>}/>
    {error && <Notice kind="error">{error}<button type="button" onClick={load} className="ml-2 font-semibold underline">Try again</button></Notice>}
    <section className="overflow-hidden rounded-2xl border border-[#e4e1da] bg-white">
      <div className="grid gap-3 border-b border-[#eeece6] p-4 sm:grid-cols-[minmax(220px,1fr)_190px_auto] sm:items-end sm:p-5"><div><label className="mb-1.5 block text-xs font-medium text-[#6d6a62]">Find a case</label><SearchField value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Case label, ID, location"/></div><SelectField label="Record status" value={status} onChange={(event) => { setStatus(event.target.value); setOffset(0); }}><option value="">All statuses</option><option value="created">Created</option><option value="image_uploaded">Image uploaded</option></SelectField><p className="text-xs text-[#858178]">Page {Math.floor(offset / 20) + 1} · {cases.length} records</p></div>
      {loading ? <Loading label="Loading cases"/> : filtered.length === 0 ? <EmptyState icon={ClipboardList} title={search ? "No cases match your search" : "No case records yet"} description={search ? "Try another case label, identifier, or location." : "Create a case record to organize a patient image."} action={!search && <Button as={Link} to="/app/cases/new"><Plus size={15}/>Create a case</Button>}/> : <div className="overflow-x-auto"><table className="w-full min-w-[780px] text-left"><thead className="border-b border-[#eeece6] bg-[#fbfaf8] text-[10px] uppercase tracking-[0.14em] text-[#89867e]"><tr><th scope="col" className="px-5 py-3 font-semibold">Case record</th>{user?.role === "clinician" && <th scope="col" className="px-4 py-3 font-semibold">Patient</th>}<th scope="col" className="px-4 py-3 font-semibold">Body location</th><th scope="col" className="px-4 py-3 font-semibold">Status</th><th scope="col" className="px-4 py-3 font-semibold">Created</th><th scope="col" className="px-4 py-3"/></tr></thead><tbody className="divide-y divide-[#efede8]">{filtered.map((item) => <tr key={item.id} className="transition hover:bg-[#fcfbf9]"><td className="px-5 py-4"><Link to={`/app/cases/${item.id}`} className="text-sm font-semibold text-[#373630] hover:text-[#a25539]">{item.case_label || "Untitled case"}</Link><p className="mt-1 max-w-[230px] truncate font-mono text-[10px] text-[#929087]">{item.id}</p></td>{user?.role === "clinician" && <td className="px-4 py-4 text-sm text-[#626057]">{patientNames[item.patient_id] || "Patient record"}</td>}<td className="px-4 py-4 text-sm text-[#626057]">{item.body_location || "Not recorded"}</td><td className="px-4 py-4"><span className="rounded-full bg-[#f1eee8] px-2.5 py-1 text-xs capitalize text-[#625e55]">{item.status?.replaceAll("_", " ")}</span></td><td className="px-4 py-4"><span className="inline-flex items-center gap-1.5 text-sm text-[#77746c]"><CalendarDays size={14}/>{dateLabel(item.created_at)}</span></td><td className="px-4 py-4 text-right"><div className="flex justify-end gap-1"><Link to={`/app/upload?case=${item.id}`} title="Add image" className="rounded-md p-2 text-[#817d73] hover:bg-[#f2efe8] hover:text-[#9e5439]"><ImagePlus size={16}/></Link><Link to={`/app/cases/${item.id}`} title="Open details" className="rounded-md p-2 text-[#817d73] hover:bg-[#f2efe8] hover:text-[#9e5439]"><ArrowRight size={16}/></Link></div></td></tr>)}</tbody></table></div>}
      <div className="flex items-center justify-between border-t border-[#eeece6] px-5 py-3"><span className="text-xs text-[#89867e]">Showing records from your account</span><div className="flex gap-2"><Button variant="secondary" disabled={!offset || loading} onClick={() => setOffset(Math.max(0, offset - 20))}>Previous</Button><Button variant="secondary" disabled={!hasNext || loading} onClick={() => setOffset(offset + 20)}>Next</Button></div></div>
    </section>
  </div>;
}

export function CreateCasePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [query] = useSearchParams();
  const patientQuery = query.get("patient");
  const [patients, setPatients] = useState([]);
  const [ownPatient, setOwnPatient] = useState(null);
  const [form, setForm] = useState({ patient_id: "", case_label: "", body_location: "", image_source: "mobile_camera", capture_date: new Date().toISOString().slice(0, 16), description: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    const request = user?.role === "clinician" ? patientApi.list({ limit: 100 }) : patientApi.me();
    request.then((result) => { if (!active) return; if (user?.role === "clinician") { setPatients(result); const selectedPatient = result.find((item) => item.id === patientQuery); if (selectedPatient) setForm((current) => ({ ...current, patient_id: selectedPatient.id })); } else { setOwnPatient(result); setForm((current) => ({ ...current, patient_id: result.id })); } }).catch((err) => { if (active && user?.role === "user" && err.response?.status !== 404) setError(errorMessage(err, "Could not load your profile.")); }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [user?.role, patientQuery]);
  async function submit(event) {
    event.preventDefault(); setSaving(true); setError("");
    try { const record = await caseApi.create({ patient_id: form.patient_id, case_label: form.case_label.trim() || null, body_location: form.body_location || null, image_source: form.image_source, capture_date: form.capture_date ? new Date(form.capture_date).toISOString() : null, description: form.description.trim() || null }); navigate(`/app/cases/${record.id}`, { replace: true, state: { created: true } }); }
    catch (err) { setError(errorMessage(err, "Could not create the case.")); }
    finally { setSaving(false); }
  }
  return <div className="mx-auto max-w-3xl space-y-6"><PageTitle eyebrow="Case records" title="Create a case" description="Add the case context needed to organize image uploads. Avoid direct identifiers in the description."/>{error && <Notice kind="error">{error}</Notice>}{loading ? <Loading label="Loading patient records"/> : user?.role === "user" && !ownPatient ? <Notice kind="warning">Create your patient profile before opening a case. <Link to="/app/profile" className="ml-1 font-semibold underline">Open profile</Link></Notice> : <form onSubmit={submit} className="space-y-5 rounded-2xl border border-[#e4e1da] bg-white p-5 sm:p-7">{user?.role === "clinician" ? <SelectField label="Patient record" required value={form.patient_id} onChange={(event) => setForm({ ...form, patient_id: event.target.value })}><option value="">Select a patient</option>{patients.map((p) => <option key={p.id} value={p.id}>{p.patient_name || p.patient_code} · {p.patient_code}</option>)}</SelectField> : <div className="rounded-lg bg-[#f5f3ee] p-3 text-sm text-[#656158]">Patient profile: {ownPatient?.patient_name || ownPatient?.patient_code}</div>}
      {user?.role === "clinician" && patients.length === 0 && <Notice kind="warning">No patient records found. <Link to="/app/patients" className="ml-1 font-semibold underline">Add a patient</Link></Notice>}
      <label className="block text-sm font-medium text-[#484640]">Case label <span className="font-normal text-[#89867e]">(optional)</span><input maxLength={100} value={form.case_label} onChange={(event) => setForm({ ...form, case_label: event.target.value })} className="mt-1.5 w-full rounded-lg border border-[#d9d6ce] px-3 py-2.5 text-sm outline-none focus:border-[#bc6747]" placeholder="e.g. Forearm image, spring visit"/></label>
      <div className="grid gap-4 sm:grid-cols-2"><label className="block text-sm font-medium text-[#484640]">Body location<select value={form.body_location} onChange={(event) => setForm({ ...form, body_location: event.target.value })} className="mt-1.5 w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 text-sm"><option value="">Not recorded</option>{["Head", "Face", "Neck", "Chest", "Back", "Abdomen", "Arm", "Forearm", "Hand", "Leg", "Foot", "Other"].map((v) => <option key={v}>{v}</option>)}</select></label><label className="block text-sm font-medium text-[#484640]">Image source<select value={form.image_source} onChange={(event) => setForm({ ...form, image_source: event.target.value })} className="mt-1.5 w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 text-sm"><option value="mobile_camera">Mobile camera</option><option value="camera">Camera</option><option value="gallery">Photo library</option><option value="other">Other</option></select></label></div>
      <label className="block text-sm font-medium text-[#484640]">Capture date<input type="datetime-local" value={form.capture_date} onChange={(event) => setForm({ ...form, capture_date: event.target.value })} className="mt-1.5 w-full rounded-lg border border-[#d9d6ce] px-3 py-2.5 text-sm"/></label>
      <label className="block text-sm font-medium text-[#484640]">Description <span className="font-normal text-[#89867e]">(de-identified)</span><textarea rows={3} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} maxLength={3000} className="mt-1.5 w-full rounded-lg border border-[#d9d6ce] px-3 py-2.5 text-sm outline-none focus:border-[#bc6747]" placeholder="Optional, non-identifying context"/></label>
      <div className="flex justify-end gap-2"><Button as={Link} to="/app/cases" variant="secondary">Cancel</Button><Button disabled={saving || loading || (user?.role === "clinician" && patients.length === 0)}>{saving ? "Creating…" : "Create case"}<ArrowRight size={15}/></Button></div>
    </form>}</div>;
}
