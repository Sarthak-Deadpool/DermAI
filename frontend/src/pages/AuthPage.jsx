import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { Activity, ArrowRight, Eye, EyeOff, LockKeyhole } from "lucide-react";
import { useAuth } from "../state/AuthContext";
import { errorMessage } from "../api/client";
import { Button, Field, Notice } from "../components/ui";

export default function AuthPage({ mode = "login" }) {
  const registerMode = mode === "register";
  const { user, loading, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  if (!loading && user) return <Navigate to="/app" replace/>;

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(""); setSuccess("");
    try {
      if (registerMode) { await register(form); setSuccess("Your account has been created. Sign in to continue."); navigate("/login", { replace: true, state: { registered: true } }); }
      else { await login({ email: form.email, password: form.password }); const next = params.get("next"); navigate(next?.startsWith("/") && !next.startsWith("//") ? next : "/app", { replace: true }); }
    } catch (err) { setError(errorMessage(err, registerMode ? "Could not create the account." : "Email or password is incorrect.")); }
    finally { setBusy(false); }
  }

  return <div className="grid min-h-screen bg-[#f7f5f0] lg:grid-cols-[1.08fr_0.92fr]">
    <section className="relative hidden overflow-hidden border-r border-[#e8e5de] bg-[#f0ede6] p-12 lg:flex lg:flex-col lg:justify-between xl:p-16"><div><Link to="/login" className="inline-flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#e5d8cc] text-[#99573c]"><Activity size={20}/></span><span className="display-serif text-2xl">DermAI</span></Link></div><div className="relative z-10 max-w-xl"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#a25a3e]">A thoughtful place for skin image records</p><h1 className="display-serif mt-5 text-6xl leading-[1.06] tracking-[-0.04em] text-[#2e2b25]">Care starts with a clearer picture.</h1><p className="mt-6 max-w-lg text-base leading-7 text-[#716c62]">Organize cases, securely add images, and keep a clear record of the work ahead.</p><div className="mt-9 flex items-center gap-3 border-t border-[#dcd7ce] pt-5 text-sm text-[#6d695f]"><LockKeyhole size={17} className="text-[#9e5e43]"/>Private, account-scoped access</div></div><div className="absolute -bottom-32 -right-24 h-[440px] w-[440px] rounded-full border border-[#d5c8b8]"/><div className="absolute -bottom-20 -right-12 h-[300px] w-[300px] rounded-full border border-[#d5c8b8]"/><p className="relative z-10 text-xs text-[#928d83]">AI-assisted screening support · not a diagnosis</p></section>
    <section className="flex min-h-screen flex-col justify-center px-5 py-10 sm:px-10 lg:px-14 xl:px-20"><div className="mx-auto w-full max-w-md"><Link to="/login" className="mb-12 inline-flex items-center gap-2 lg:hidden"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#e5d8cc] text-[#99573c]"><Activity size={18}/></span><span className="display-serif text-xl">DermAI</span></Link><p className="text-xs font-semibold uppercase tracking-[0.15em] text-[#a25a3e]">{registerMode ? "Get started" : "Welcome back"}</p><h2 className="display-serif mt-2 text-4xl tracking-[-0.03em]">{registerMode ? "Create your account" : "Sign in to DermAI"}</h2><p className="mt-2 text-sm text-[#79766d]">{registerMode ? "Registration creates a general user account." : "Use your account email and password to continue."}</p>
      {error && <Notice kind="error" className="mt-6">{error}</Notice>}{success && <Notice kind="success" className="mt-6">{success}</Notice>}{location.state?.registered && <Notice kind="success" className="mt-6">Your account is ready. Sign in to continue.</Notice>}
      <form onSubmit={submit} className="mt-8 space-y-5">{registerMode && <Field label="Your name" autoComplete="username" minLength={3} maxLength={50} required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} placeholder="How should we address you?"/>}<Field label="Email address" type="email" autoComplete="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@example.com"/><label className="block text-sm font-medium text-[#484640]">Password<div className="relative mt-1.5"><input type={showPassword ? "text" : "password"} autoComplete={registerMode ? "new-password" : "current-password"} minLength={registerMode ? 8 : 1} maxLength={128} required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 pr-11 text-sm outline-none focus:border-[#bc6747] focus:ring-4 focus:ring-[#bd6545]/10" placeholder="••••••••"/><button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(!showPassword)} className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-2 text-[#77746c]">{showPassword ? <EyeOff size={16}/> : <Eye size={16}/>}</button></div></label><Button disabled={busy} className="w-full">{busy ? "Please wait…" : registerMode ? "Create account" : "Sign in"}<ArrowRight size={16}/></Button></form>
      <p className="mt-6 text-center text-sm text-[#77746c]">{registerMode ? "Already have an account?" : "New to DermAI?"} <Link className="font-semibold text-[#9c5438] hover:underline" to={registerMode ? "/login" : "/register"}>{registerMode ? "Sign in" : "Create an account"}</Link></p><p className="mt-10 text-center text-xs leading-5 text-[#969187]">DermAI supports secure image intake and case organization. It does not provide a standalone medical diagnosis.</p>
    </div></section>
  </div>;
}
