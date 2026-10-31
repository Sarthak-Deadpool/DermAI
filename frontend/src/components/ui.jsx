import { AlertCircle, LoaderCircle, Search } from "lucide-react";

export function Button({ children, variant = "primary", className = "", disabled, as: Element = "button", ...props }) {
  const styles = {
    primary: "bg-[#bd6545] text-white hover:bg-[#a95235]",
    secondary: "border border-[#dedbd4] bg-white text-[#373530] hover:bg-[#f5f3ee]",
    quiet: "text-[#5a5852] hover:bg-[#efede7]",
    danger: "border border-red-200 bg-white text-red-700 hover:bg-red-50",
  };
  const elementProps = Element === "button" ? { disabled, ...props } : props;
  return <Element className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`} {...elementProps}>{children}</Element>;
}

export function Field({ label, hint, error, className = "", ...props }) {
  return <label className={`block text-sm font-medium text-[#484640] ${className}`}>{label}{hint && <span className="ml-1 font-normal text-[#89867e]">{hint}</span>}<input aria-invalid={Boolean(error)} className="mt-1.5 w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 text-sm text-[#292823] placeholder:text-[#a4a198] outline-none transition focus:border-[#bc6747] focus:ring-4 focus:ring-[#bd6545]/10" {...props}/>{error && <span className="mt-1 block text-xs text-red-700">{error}</span>}</label>;
}

export function SelectField({ label, children, className = "", ...props }) {
  return <label className="block text-sm font-medium text-[#484640]">{label}<select className={`mt-1.5 w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 text-sm text-[#292823] outline-none focus:border-[#bc6747] focus:ring-4 focus:ring-[#bd6545]/10 ${className}`} {...props}>{children}</select></label>;
}

export function TextareaField({ label, hint, className = "", ...props }) {
  return <label className={`block text-sm font-medium text-[#484640]`}>{label}{hint && <span className="ml-1 font-normal text-[#89867e]">{hint}</span>}<textarea className={`mt-1.5 w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 text-sm text-[#292823] outline-none focus:border-[#bc6747] focus:ring-4 focus:ring-[#bd6545]/10 ${className}`} {...props}/></label>;
}

export function Notice({ children, kind = "info", className = "" }) {
  const styles = { info: "border-[#ded8cd] bg-[#f2efe8] text-[#514d45]", success: "border-emerald-200 bg-emerald-50 text-emerald-900", warning: "border-amber-200 bg-amber-50 text-amber-900", error: "border-red-200 bg-red-50 text-red-800" };
  return <div role={kind === "error" ? "alert" : "status"} className={`flex items-start gap-2.5 rounded-lg border px-4 py-3 text-sm leading-6 ${styles[kind]} ${className}`}>{kind === "error" && <AlertCircle size={17} className="mt-1 shrink-0"/>}<div>{children}</div></div>;
}

export function PageTitle({ eyebrow, title, description, action }) {
  return <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#a25a3e]">{eyebrow}</p><h1 className="display-serif mt-1 text-4xl font-medium tracking-[-0.035em] text-[#292823]">{title}</h1>{description && <p className="mt-2 max-w-2xl text-sm leading-6 text-[#716e66]">{description}</p>}</div>{action}</div>;
}

export function SectionHeading({ title, description, action }) {
  return <div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-base font-semibold text-[#302f2a]">{title}</h2>{description && <p className="mt-1 text-sm text-[#7a776f]">{description}</p>}</div>{action}</div>;
}

export function Loading({ label = "Loading workspace" }) {
  return <div role="status" className="flex min-h-44 items-center justify-center gap-2 text-sm text-[#77746c]"><LoaderCircle className="animate-spin" size={18}/>{label}</div>;
}

export function SearchField({ value, onChange, placeholder = "Search", ...props }) {
  return <label className="relative block"><Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8c8981]"/><input type="search" value={value} onChange={onChange} placeholder={placeholder} className="min-h-10 w-full rounded-lg border border-[#dedbd4] bg-white pl-9 pr-3 text-sm outline-none placeholder:text-[#9b988f] focus:border-[#bc6747] focus:ring-4 focus:ring-[#bd6545]/10" {...props}/></label>;
}

export function Metric({ label, value, detail, icon: Icon }) {
  return <article className="rounded-xl border border-[#e4e1da] bg-white p-4"><div className="flex items-start justify-between"><div><p className="text-xs font-medium text-[#77746c]">{label}</p><p className="mt-2 text-2xl font-semibold tracking-tight text-[#2f2e29]">{value}</p></div>{Icon && <span className="rounded-lg bg-[#f4eee8] p-2 text-[#a25a3e]"><Icon size={17}/></span>}</div>{detail && <p className="mt-2 text-xs text-[#858178]">{detail}</p>}</article>;
}

export function EmptyState({ title, description, action, icon: Icon }) {
  return <div className="px-6 py-14 text-center">{Icon && <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-[#f2efe8] text-[#8b6a58]"><Icon size={22}/></span>}<h3 className="mt-4 text-sm font-semibold text-[#33322d]">{title}</h3><p className="mx-auto mt-1 max-w-md text-sm leading-6 text-[#78756d]">{description}</p>{action && <div className="mt-5">{action}</div>}</div>;
}

export const inputClass = "mt-1.5 w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 text-sm text-[#292823] outline-none focus:border-[#bc6747] focus:ring-4 focus:ring-[#bd6545]/10";
