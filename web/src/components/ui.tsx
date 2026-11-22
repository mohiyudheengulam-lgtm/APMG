"use client";

import { AlertTriangle, CheckCircle2, Clock, Flag as FlagIcon, Loader2 } from "lucide-react";
import { FLAG_LABEL } from "@/lib/api";

export function PageHeader({ title, sub, right }: { title: string; sub?: string; right?: React.ReactNode }) {
  return (
    <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-[34px] leading-[1.1] font-extrabold tracking-[-0.02em] text-ink">{title}</h1>
        {sub && <p className="mt-2 max-w-2xl text-[15px] text-ink-2">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

export function Card({ title, right, children, className = "" }: { title?: string; right?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={`tile p-6 ${className}`}>
      {(title || right) && (
        <div className="mb-4 flex items-center justify-between gap-2">
          {title && <h2 className="text-[17px] font-bold tracking-tight text-ink">{title}</h2>}
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function Kpi({ label, value, sub, accent }: { label: string; value: React.ReactNode; sub?: React.ReactNode; accent?: boolean }) {
  return (
    <div className={`tile relative overflow-hidden px-6 py-5 ${accent ? "bg-primary! text-on-primary" : ""}`}>
      <div className={`text-sm font-medium ${accent ? "text-on-primary/75" : "text-ink-2"}`}>{label}</div>
      <div className={`num mt-2 text-[36px] leading-none font-extrabold tracking-[-0.03em] ${accent ? "text-on-primary" : "text-ink"}`}>{value}</div>
      <div className={`mt-2 min-h-4 text-[13px] ${accent ? "text-on-primary/75" : "text-ink-2"}`}>{sub}</div>
    </div>
  );
}

export function FlagChips({ recommendation, flags }: { recommendation: string | null; flags?: string[] }) {
  if (recommendation == null)
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-warn-soft px-3 py-1 text-xs font-semibold text-warn">
        <AlertTriangle size={12} /> No valid result
      </span>
    );
  if (recommendation === "NO_DISCREPANCY")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-good-soft px-3 py-1 text-xs font-semibold text-good">
        <CheckCircle2 size={12} /> No discrepancy
      </span>
    );
  const list = flags ?? recommendation.split(",");
  return (
    <span className="inline-flex flex-wrap gap-1">
      {list.map((f) => (
        <span key={f} className="inline-flex items-center gap-1 rounded-full bg-bad-soft px-3 py-1 text-xs font-semibold text-bad">
          <FlagIcon size={11} /> {FLAG_LABEL[f] ?? f}
        </span>
      ))}
    </span>
  );
}

export function ReviewPill({ state, decision }: { state: string; decision: string | null }) {
  if (state === "PENDING_REVIEW")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-3 py-1 text-xs font-semibold text-ink">
        <Clock size={12} /> Pending review
      </span>
    );
  const style =
    decision === "APPROVED" ? "bg-good-soft text-good" : decision === "REJECTED" ? "bg-bad-soft text-bad" : "bg-warn-soft text-warn";
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${style}`}>{decision}</span>;
}

export function PathBadge({ path }: { path: string }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full bg-surface px-2.5 py-1 text-xs font-semibold text-ink"
      title={path === "A" ? "Vector RAG" : "OKF navigation"}
    >
      <span className="h-2 w-2 rounded-full" style={{ background: path === "A" ? "var(--series-a)" : "var(--series-b)" }} />
      {path === "A" ? "A · RAG" : "B · OKF"}
    </span>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl border border-dashed border-line-strong px-4 py-10 text-center text-sm text-ink-2">{children}</div>;
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
    <div className="mb-5 rounded-2xl bg-bad-soft px-5 py-3 text-sm text-bad">
      {error.includes("fetch") || error.includes("Internal Server Error") || error.includes("ECONNREFUSED")
        ? "Cannot reach the local API. Start it with: uv run uvicorn agent_on_duty.api:app --port 8000"
        : error}
    </div>
  );
}
