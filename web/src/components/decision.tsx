"use client";

import { useState } from "react";
import { api } from "@/lib/api";

const CHOICES = [
  { v: "APPROVED", label: "Confirm recommendation", style: "border-good text-good" },
  { v: "OVERRIDDEN", label: "Override", style: "border-warn text-warn" },
  { v: "REJECTED", label: "Reject invoice", style: "border-bad text-bad" },
] as const;

/** Manager decision — the only UI path to /decision, which calls audit.store.approve(). */
export function DecisionForm({ id, source, onDone }: { id: string; source: string; onDone: () => void }) {
  const [reviewer, setReviewer] = useState("");
  const [decision, setDecision] = useState<(typeof CHOICES)[number]["v"]>("APPROVED");
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const [busy, setBusy] = useState(false);

  async function submit() {
    setErr(undefined);
    if (!reviewer.trim()) return setErr("Reviewer name is required.");
    if (decision === "OVERRIDDEN" && !reason.trim()) return setErr("An override needs a written reason.");
    setBusy(true);
    try {
      await api(`/api/verifications/${id}/decision?source=${encodeURIComponent(source)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, reviewer, override_reason: reason || null }),
      });
      onDone();
    } catch (e) {
      setErr(String(e instanceof Error ? e.message : e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-3">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-2">Manager decision</div>
      <div className="mb-2 flex flex-wrap gap-2">
        {CHOICES.map((c) => (
          <button
            key={c.v}
            onClick={() => setDecision(c.v)}
            className={`rounded-xl border px-3 py-1.5 text-xs font-semibold ${decision === c.v ? `${c.style} bg-white shadow-sm` : "border-line text-ink-2 hover:bg-white"}`}
          >
            {c.label}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} placeholder="Reviewer name" className="w-48 rounded-xl border border-line bg-white px-2 py-1.5 text-sm" />
        <input
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder={decision === "OVERRIDDEN" ? "Override reason (required)" : "Comment / reason (optional)"}
          className="min-w-0 flex-1 rounded-xl border border-line bg-white px-2 py-1.5 text-sm"
        />
        <button onClick={submit} disabled={busy} className="btn-primary px-4 py-1.5 text-sm font-semibold">
          Record decision
        </button>
      </div>
      {err && <p className="mt-2 text-xs text-bad">{err}</p>}
    </div>
  );
}
