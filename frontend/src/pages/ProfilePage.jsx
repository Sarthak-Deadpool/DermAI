import { useEffect, useState } from "react";
import { MonitorSmartphone, ShieldCheck, UserRound } from "lucide-react";
import { authApi, patientApi } from "../api/services";
import { errorMessage } from "../api/client";
import { useAuth } from "../state/AuthContext";
import { Button, Field, Loading, Notice, PageTitle, SelectField } from "../components/ui";

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [form, setForm] = useState({ patient_name: "", age: "", gender: "prefer_not_to_say", fitzpatrick_type: "" });
  const [username, setUsername] = useState(user?.username || "");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadSessions() { try { setSessions(await authApi.sessions()); } catch (err) { setError(errorMessage(err, "Could not load active sessions.")); } }
  useEffect(() => {
    let active = true;
    const calls = [authApi.sessions()];
    if (user?.role === "user") calls.push(patientApi.me().catch((err) => err.response?.status === 404 ? null : Promise.reject(err)));
    Promise.all(calls).then((results) => { if (!active) return; setSessions(results[0]); if (user?.role === "user") { const current = results[1]; setProfile(current); if (current) setForm({ patient_name: current.patient_name || "", age: String(current.age), gender: current.gender || "prefer_not_to_say", fitzpatrick_type: current.fitzpatrick_type || "" }); } }).catch((err) => { if (active) setError(errorMessage(err, "Could not load profile settings.")); }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [user?.role]);

  async function saveUsername(event) {
    event.preventDefault(); setSaving(true); setError(""); setNotice("");
    try { const updated = await authApi.updateMe({ username: username.trim() }); setUser(updated); setNotice("Account name updated."); }
    catch (err) { setError(errorMessage(err, "Could not update your account.")); }
    finally { setSaving(false); }
  }
  async function saveProfile(event) {
    event.preventDefault(); setSaving(true); setError(""); setNotice("");
    const payload = { age: Number(form.age), gender: form.gender, ...(form.patient_name.trim() ? { patient_name: form.patient_name.trim() } : {}), ...(form.fitzpatrick_type ? { fitzpatrick_type: form.fitzpatrick_type } : {}) };
    try { const updated = profile ? await patientApi.updateMe(payload) : await patientApi.createMe(payload); setProfile(updated); setNotice(profile ? "Patient profile updated." : "Patient profile created."); }
    catch (err) { setError(errorMessage(err, "Could not save your patient profile.")); }
    finally { setSaving(false); }
  }
  async function revoke(id) {
    setError(""); setNotice("");
    try { await authApi.revokeSession(id); setNotice("Session revoked."); await loadSessions(); }
    catch (err) { setError(errorMessage(err, "Could not revoke that session.")); }
  }
  async function revokeOthers() {
    setError("");
    try { const result = await authApi.revokeOthers(); setNotice(`${result.revoked_count} other session${result.revoked_count === 1 ? "" : "s"} revoked.`); await loadSessions(); }
    catch (err) { setError(errorMessage(err, "Could not revoke other sessions.")); }
  }
  async function logoutEverywhere() {
    if (!window.confirm("Sign out of all active sessions, including this device?")) return;
    try { await authApi.logoutAll(); window.location.assign("/login"); }
    catch (err) { setError(errorMessage(err, "Could not revoke all sessions.")); }
  }

  if (loading) return <Loading label="Loading account settings"/>;
  return <div className="mx-auto max-w-4xl space-y-7"><PageTitle eyebrow="Account settings" title="Your profile" description="Update account details and review active sessions."/>{error && <Notice kind="error">{error}</Notice>}{notice && <Notice kind="success">{notice}</Notice>}
    <form onSubmit={saveUsername} className="space-y-5 rounded-2xl border border-[#e4e1da] bg-white p-5 sm:p-7"><div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f1e9e1] text-[#97563c]"><UserRound size={18}/></span><div><h2 className="font-semibold">Account information</h2><p className="mt-1 text-xs text-[#89867e]">{user?.email} · {user?.role?.replaceAll("_", " ")}</p></div></div><Field label="Display name" minLength={3} maxLength={50} required value={username} onChange={(event) => setUsername(event.target.value)}/><Button disabled={saving}>Save account details</Button></form>
    {user?.role === "user" && <form onSubmit={saveProfile} className="space-y-5 rounded-2xl border border-[#e4e1da] bg-white p-5 sm:p-7"><div><h2 className="font-semibold">Patient profile</h2><p className="mt-1 text-sm text-[#77746c]">This profile is associated with your account and is used when creating your cases.</p></div><div className="grid gap-4 sm:grid-cols-2"><Field label="Patient name" maxLength={150} autoComplete="off" value={form.patient_name} onChange={(event) => setForm({ ...form, patient_name: event.target.value })} placeholder="Optional"/><Field label="Age" type="number" min="0" max="120" required value={form.age} onChange={(event) => setForm({ ...form, age: event.target.value })}/><SelectField label="Gender" value={form.gender} onChange={(event) => setForm({ ...form, gender: event.target.value })}>{["female", "male", "non_binary", "other", "prefer_not_to_say", "unknown"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</SelectField><SelectField label="Fitzpatrick skin type" value={form.fitzpatrick_type} onChange={(event) => setForm({ ...form, fitzpatrick_type: event.target.value })}><option value="">Not recorded</option>{["I", "II", "III", "IV", "V", "VI"].map((value) => <option key={value}>{value}</option>)}</SelectField></div><p className="text-xs leading-5 text-[#89867e]">Patient names are identifiable health data. Use only your authorized information.</p><Button disabled={saving}>{profile ? "Save patient profile" : "Create patient profile"}</Button></form>}
    <section className="rounded-2xl border border-[#e4e1da] bg-white p-5 sm:p-7"><div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f1e9e1] text-[#97563c]"><MonitorSmartphone size={18}/></span><div><h2 className="font-semibold">Active sessions</h2><p className="mt-1 text-xs text-[#89867e]">Review the sessions currently associated with your account.</p></div></div><Button variant="secondary" onClick={revokeOthers}>Sign out other sessions</Button></div>{sessions.length === 0 ? <p className="mt-5 text-sm text-[#77746c]">No active sessions returned.</p> : <ul className="mt-5 divide-y divide-[#efede8]">{sessions.map((session) => <li key={session.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div><p className="flex items-center gap-2 text-sm font-semibold">{session.is_current ? "This device" : "Active session"}{session.is_current && <span className="rounded-full bg-[#f1eee8] px-2 py-0.5 text-[10px] font-medium">Current</span>}</p><p className="mt-1 text-xs text-[#817d73]">Last active {new Date(session.last_seen_at).toLocaleString()} · Expires {new Date(session.absolute_expires_at).toLocaleString()}</p></div><Button variant="quiet" onClick={() => revoke(session.id)}>Revoke</Button></li>)}</ul>}<div className="mt-4 flex items-center gap-2 border-t border-[#efede8] pt-4 text-sm text-[#817d73]"><ShieldCheck size={16}/>Session security is managed by the DermAI backend.</div><Button variant="danger" className="mt-4" onClick={logoutEverywhere}>Sign out everywhere</Button></section>
  </div>;
}
