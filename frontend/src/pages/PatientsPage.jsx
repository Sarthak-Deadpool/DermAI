import { useEffect, useState } from "react";
import { Archive, ArrowRight, ClipboardList, Plus, Search, Users } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { caseApi, patientApi } from "../api/services";
import { errorMessage } from "../api/client";
import { Button, EmptyState, Field, Loading, Notice, PageTitle, SearchField, SelectField, TextareaField } from "../components/ui";

const emptyPatient = { patient_name: "", age: "", gender: "prefer_not_to_say", medical_history: "", known_allergies: "", fitzpatrick_type: "" };
const skinTypes = ["I", "II", "III", "IV", "V", "VI"];

export default function PatientsPage() {
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [openForm, setOpenForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyPatient);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setLoading(true); setError("");
    try { const result = await patientApi.list({ offset, limit: 20, ...(search.length ? { search } : {}) }); setPatients(result); setHasNext(result.length === 20); }
    catch (err) { setError(errorMessage(err, "Could not load patient records.")); }
    finally { setLoading(false); }
  }
  useEffect(() => {
    let active = true;
    patientApi.list({ offset, limit: 20, ...(search.length ? { search } : {}) }).then((result) => { if (active) { setPatients(result); setHasNext(result.length === 20); } }).catch((err) => { if (active) setError(errorMessage(err, "Could not load patient records.")); }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [offset, search]);

  function startEdit(patient) {
    setEditing(patient.id); setOpenForm(true); setError("");
    setForm({ patient_name: patient.patient_name || "", age: String(patient.age), gender: patient.gender || "prefer_not_to_say", medical_history: patient.medical_history || "", known_allergies: patient.known_allergies || "", fitzpatrick_type: patient.fitzpatrick_type || "" });
  }
  function closeForm() { setOpenForm(false); setEditing(null); setForm(emptyPatient); }
  async function submit(event) {
    event.preventDefault(); setError(""); setNotice("");
    const payload = { patient_name: form.patient_name.trim() || null, age: Number(form.age), gender: form.gender, medical_history: form.medical_history.trim() || null, known_allergies: form.known_allergies.trim() || null, fitzpatrick_type: form.fitzpatrick_type || null };
    try { if (editing) await patientApi.update(editing, payload); else await patientApi.create(payload); setNotice(editing ? "Patient record updated." : "Patient record created."); closeForm(); await load(); }
    catch (err) { setError(errorMessage(err, "Could not save the patient record.")); }
  }
  async function archive(patient) {
    if (!window.confirm(`Archive patient ${patient.patient_code}? Existing cases will remain.`)) return;
    setError("");
    try { await patientApi.archive(patient.id); setNotice("Patient record archived. Existing cases remain in your case list."); await load(); }
    catch (err) { setError(errorMessage(err, "Could not archive this patient.")); }
  }

  return <div className="space-y-7"><PageTitle eyebrow="Clinical records" title="Patients" description="Manage patient records assigned to your clinician account. Patient names are identifiable health data; keep them out of free-text notes." action={<Button onClick={() => { setOpenForm(!openForm); setEditing(null); setForm(emptyPatient); }}><Plus size={16}/>{openForm ? "Close form" : "Add patient"}</Button>}/>
    <Notice kind="warning">Only enter patient names when authorized. Medical history and allergy fields must remain de-identified; do not enter names, phone numbers, or email addresses in free text.</Notice>
    {notice && <Notice kind="success">{notice}</Notice>}{error && <Notice kind="error">{error}</Notice>}
    {openForm && <form onSubmit={submit} className="space-y-5 rounded-2xl border border-[#e4e1da] bg-white p-5 sm:p-7"><div><h2 className="font-semibold">{editing ? "Edit patient" : "New patient record"}</h2><p className="mt-1 text-sm text-[#77746c]">Use the fields needed for case organization. All fields are sent to the existing patient API.</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><Field label="Patient name" maxLength={150} autoComplete="off" value={form.patient_name} onChange={(event) => setForm({ ...form, patient_name: event.target.value })} placeholder="Optional"/><Field label="Age" required type="number" min="0" max="120" value={form.age} onChange={(event) => setForm({ ...form, age: event.target.value })}/><SelectField label="Gender" value={form.gender} onChange={(event) => setForm({ ...form, gender: event.target.value })}>{["female", "male", "non_binary", "other", "prefer_not_to_say", "unknown"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</SelectField><TextareaField label="Medical history" hint="· de-identified" maxLength={2000} rows={3} value={form.medical_history} onChange={(event) => setForm({ ...form, medical_history: event.target.value })}/><TextareaField label="Known allergies" hint="· de-identified" maxLength={1000} rows={3} value={form.known_allergies} onChange={(event) => setForm({ ...form, known_allergies: event.target.value })}/><SelectField label="Fitzpatrick skin type" value={form.fitzpatrick_type} onChange={(event) => setForm({ ...form, fitzpatrick_type: event.target.value })}><option value="">Not recorded</option>{skinTypes.map((type) => <option key={type}>{type}</option>)}</SelectField></div><div className="flex gap-2"><Button>{editing ? "Save changes" : "Create patient"}</Button><Button type="button" variant="secondary" onClick={closeForm}>Cancel</Button></div></form>}
    <section className="overflow-hidden rounded-2xl border border-[#e4e1da] bg-white"><div className="flex flex-wrap items-end justify-between gap-4 border-b border-[#eeece6] p-4 sm:p-5"><div><h2 className="font-semibold">Patient directory</h2><p className="mt-1 text-xs text-[#89867e]">{patients.length} records on this page · search by patient code</p></div><div className="w-full sm:max-w-xs"><SearchField value={search} onChange={(event) => { setSearch(event.target.value.slice(0, 40)); setOffset(0); }} placeholder="Search patient code" aria-label="Search patients by code"/></div></div>
      {loading ? <Loading label="Loading patient records"/> : patients.length === 0 ? <EmptyState icon={Users} title={search ? "No matching patient records" : "No patient records yet"} description={search ? "Try another patient code or clear your search." : "Create a patient record to start organizing their cases."} action={!search && <Button onClick={() => setOpenForm(true)}><Plus size={15}/>Add patient</Button>}/> : <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left"><thead className="border-b border-[#eeece6] bg-[#fbfaf8] text-[10px] uppercase tracking-[0.14em] text-[#89867e]"><tr><th className="px-5 py-3 font-semibold">Patient</th><th className="px-4 py-3 font-semibold">Age</th><th className="px-4 py-3 font-semibold">Gender</th><th className="px-4 py-3 font-semibold">Skin type</th><th className="px-4 py-3 text-right font-semibold">Actions</th></tr></thead><tbody className="divide-y divide-[#efede8]">{patients.map((patient) => <tr key={patient.id} className="hover:bg-[#fcfbf9]"><td className="px-5 py-3.5"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#f1e9e1] text-sm font-semibold text-[#97563c]">{(patient.patient_name || patient.patient_code || "P").slice(0, 1).toUpperCase()}</span><div><Link to={`/app/patients/${patient.id}`} className="text-sm font-semibold text-[#393832] hover:text-[#a25539]">{patient.patient_name || "Name not recorded"}</Link><p className="mt-0.5 font-mono text-[10px] text-[#8b887f]">{patient.patient_code}</p></div></div></td><td className="px-4 py-3.5 text-sm text-[#625f57]">{patient.age}</td><td className="px-4 py-3.5 text-sm capitalize text-[#625f57]">{patient.gender?.replaceAll("_", " ")}</td><td className="px-4 py-3.5 text-sm text-[#625f57]">{patient.fitzpatrick_type || "Not recorded"}</td><td className="px-4 py-3.5"><div className="flex justify-end gap-1"><Link to={`/app/patients/${patient.id}`} className="rounded-md px-2.5 py-2 text-xs font-semibold text-[#68655d] hover:bg-[#f2efe8]">Details</Link><Link to={`/app/cases/new?patient=${patient.id}`} className="inline-flex items-center gap-1 rounded-md px-2.5 py-2 text-xs font-semibold text-[#9e5439] hover:bg-[#f6eee8]">New case <ArrowRight size={13}/></Link><button type="button" onClick={() => startEdit(patient)} aria-label={`Edit ${patient.patient_code}`} className="rounded-md px-2.5 py-2 text-xs font-semibold text-[#68655d] hover:bg-[#f2efe8]">Edit</button><button type="button" onClick={() => archive(patient)} aria-label={`Archive ${patient.patient_code}`} className="rounded-md p-2 text-[#817d73] hover:bg-red-50 hover:text-red-700"><Archive size={15}/></button></div></td></tr>)}</tbody></table></div>}
      <div className="flex items-center justify-between border-t border-[#eeece6] px-5 py-3"><span className="text-xs text-[#89867e]">Page {Math.floor(offset / 20) + 1}</span><div className="flex gap-2"><Button variant="secondary" disabled={!offset || loading} onClick={() => setOffset(Math.max(0, offset - 20))}>Previous</Button><Button variant="secondary" disabled={!hasNext || loading} onClick={() => setOffset(offset + 20)}>Next</Button></div></div>
    </section>
  </div>;
}

export function PatientDetailPage() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([patientApi.get(patientId), caseApi.forPatient(patientId)]).then(([current, records]) => { if (active) { setPatient(current); setCases(records); } }).catch((err) => { if (active) setError(errorMessage(err, "Could not load this patient record.")); }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [patientId]);
  if (loading) return <Loading label="Loading patient record"/>;
  if (error) return <div className="space-y-5"><PageTitle eyebrow="Clinical records" title="Patient details"/><Notice kind="error">{error}</Notice><Link to="/app/patients" className="text-sm font-semibold text-[#a25539]">Back to patients</Link></div>;
  return <div className="space-y-6"><PageTitle eyebrow="Patient record" title={patient?.patient_name || patient?.patient_code || "Patient details"} description={`Patient code ${patient?.patient_code}. This record is visible to its assigned clinician.`} action={<Button as={Link} to={`/app/cases/new?patient=${patientId}`}><Plus size={15}/>New case</Button>}/><div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(300px,0.75fr)]"><section className="rounded-2xl border border-[#e4e1da] bg-white p-5"><h2 className="font-semibold">Demographic details</h2><dl className="mt-4 grid grid-cols-2 gap-x-5 gap-y-5"><Detail label="Age" value={patient?.age}/><Detail label="Gender" value={patient?.gender?.replaceAll("_", " ")}/><Detail label="Fitzpatrick type" value={patient?.fitzpatrick_type}/><Detail label="Created" value={patient?.created_at ? new Date(patient.created_at).toLocaleDateString() : null}/></dl></section><section className="rounded-2xl border border-[#e4e1da] bg-white p-5"><h2 className="font-semibold">Clinical context</h2><div className="mt-4 space-y-4"><div><p className="text-xs text-[#89867e]">Medical history · de-identified</p><p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-[#514f49]">{patient?.medical_history || "Not recorded"}</p></div><div><p className="text-xs text-[#89867e]">Known allergies · de-identified</p><p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-[#514f49]">{patient?.known_allergies || "Not recorded"}</p></div></div></section></div><section className="overflow-hidden rounded-2xl border border-[#e4e1da] bg-white"><div className="flex items-center justify-between border-b border-[#eeece6] p-5"><div><h2 className="font-semibold">Cases</h2><p className="mt-1 text-xs text-[#89867e]">{cases.length} case records returned</p></div></div>{cases.length ? <div className="divide-y divide-[#efede8]">{cases.map((item) => <Link key={item.id} to={`/app/cases/${item.id}`} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 hover:bg-[#fcfbf9]"><div><p className="text-sm font-semibold">{item.case_label || "Untitled case"}</p><p className="mt-1 text-xs text-[#817d73]">{item.body_location || "Location not recorded"} · {item.created_at ? new Date(item.created_at).toLocaleDateString() : "Date unavailable"}</p></div><span className="rounded-full bg-[#f1eee8] px-2.5 py-1 text-xs capitalize text-[#625e55]">{item.status?.replaceAll("_", " ")}</span></Link>)}</div> : <EmptyState icon={ClipboardList} title="No cases for this patient" description="Create a case to begin recording image intake." action={<Button as={Link} to={`/app/cases/new?patient=${patientId}`}><Plus size={15}/>Create a case</Button>}/>}</section><Link to="/app/patients" className="inline-block text-sm font-semibold text-[#a25539]">← Back to patients</Link></div>;
}

function Detail({ label, value }) { return <div><dt className="text-xs font-medium uppercase tracking-wide text-[#89867e]">{label}</dt><dd className="mt-1 text-sm capitalize text-[#393832]">{value || "Not recorded"}</dd></div>; }
