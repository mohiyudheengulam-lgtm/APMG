"use client";

import { AlertTriangle, CheckCircle2, Clock, Flag as FlagIcon, Loader2 } from "lucide-react";
import { FLAG_LABEL } from "@/lib/api";

export function PageHeader({ title, sub, right }: { title: string; sub?: string; right?: React.ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold text-ink">{title}</h1>
        {sub && <p className="mt-0.5 text-[13px] text-ink-2">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

export function Card({ title, right, children, className = "" }: { title?: string; right?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={`tile p-4 ${className}`}>
      {(title || right) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          {title && <h2 className="text-sm font-semibold text-ink">{title}</h2>}
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function Kpi({ label, value, sub, accent }: { label: string; value: React.ReactNode; sub?: React.ReactNode; accent?: boolean }) {
  return (
    <div className={`tile relative overflow-hidden px-4 py-3 ${accent ? "pl-5" : ""}`}>
      {accent && <span className="absolute inset-y-3 left-0 w-1 rounded-r bg-accent" aria-hidden />}
      <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-2">{label}</div>
      <div className="mt-1 text-[28px] leading-tight font-semibold text-ink">{value}</div>
      <div className="mt-0.5 min-h-4 text-xs text-ink-2">{sub}</div>
    </div>
  );
}

export function FlagChips({ recommendation, flags }: { recommendation: string | null; flags?: string[] }) {
  if (recommendation == null)
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-[#fff4ce] px-2.5 py-0.5 text-xs font-semibold text-[#8a6d00]">
        <AlertTriangle size={12} /> No valid result
      </span>
    );
  if (recommendation === "NO_DISCREPANCY")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-[#dff6dd] px-2.5 py-0.5 text-xs font-semibold text-[#107c10]">
        <CheckCircle2 size={12} /> No discrepancy
      </span>
    );
  const list = flags ?? recommendation.split(",");
  return (
    <span className="inline-flex flex-wrap gap-1">
      {list.map((f) => (
        <span key={f} className="inline-flex items-center gap-1 rounded-full bg-[#fde7e9] px-2.5 py-0.5 text-xs font-semibold text-[#a4262c]">
          <FlagIcon size={11} /> {FLAG_LABEL[f] ?? f}
        </span>
      ))}
    </span>
  );
}

export function ReviewPill({ state, decision }: { state: string; decision: string | null }) {
  if (state === "PENDING_REVIEW")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-[#edebe9] px-2.5 py-0.5 text-xs font-semibold text-[#323130]">
        <Clock size={12} /> Pending review
      </span>
    );
  const style =
    decision === "APPROVED" ? "bg-[#dff6dd] text-[#107c10]" : decision === "REJECTED" ? "bg-[#fde7e9] text-[#a4262c]" : "bg-[#fff4ce] text-[#8a6d00]";
  return <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${style}`}>{decision}</span>;
}

export function PathBadge({ path }: { path: string }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded border border-line bg-white px-1.5 py-0.5 text-xs font-semibold text-ink"
      title={path === "A" ? "Vector RAG" : "OKF navigation"}
    >
      <span className="h-2 w-2 rounded-full" style={{ background: path === "A" ? "var(--series-a)" : "var(--series-b)" }} />
      {path === "A" ? "A · RAG" : "B · OKF"}
    </span>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="rounded border border-dashed border-line px-4 py-8 text-center text-sm text-ink-2">{children}</div>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-ink-2">
      <Loader2 size={16} className="animate-spin" /> {label}
    </span>
  );
}

export function ErrorNote({ error }: { error?: string }) {
  if (!error) return null;
  return (
    <div className="mb-4 rounded border border-[#f1bbbc] bg-[#fde7e9] px-4 py-2 text-sm text-[#a4262c]">
      {error.includes("fetch") || error.includes("Internal Server Error") || error.includes("ECONNREFUSED")
        ? "Cannot reach the local API. Start it with: uv run uvicorn agent_on_duty.api:app --port 8000"
        : error}
    </div>
  );
}
