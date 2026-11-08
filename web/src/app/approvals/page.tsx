"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Audit, VerificationRow, useApi } from "@/lib/api";
import { eur, num, when } from "@/lib/format";
import { useSource } from "@/components/source";
import { Card, Empty, ErrorNote, FlagChips, Kpi, PageHeader, PathBadge, ReviewPill, Spinner } from "@/components/ui";
import { Findings } from "@/components/evidence";
import { DecisionForm } from "@/components/decision";

export default function ApprovalsPage() {
  const { source } = useSource();
  const { data: rows, error, loading, reload } = useApi<VerificationRow[]>(`/api/verifications?source=${encodeURIComponent(source)}`, 10000);
  const [only, setOnly] = useState<"flagged" | "all">("flagged");

  if (loading && !rows) return <Spinner label="Loading…" />;
  const all = rows ?? [];
  const pending = all
    .filter((r) => r.review_state === "PENDING_REVIEW" && (only === "all" || r.flags.length || r.recommendation == null))
    .sort((a, b) => b.impact_eur - a.impact_eur);
  const reviewed = all.filter((r) => r.review_state === "REVIEWED");

  return (
    <>
      <PageHeader
        title="Manager approvals"
        sub="Human-in-the-loop gate: the agent recommends; only a recorded manager decision is final."
        right={
          <div className="inline-flex gap-1 rounded-full bg-surface-2 p-1 text-xs font-semibold">
            {(["flagged", "all"] as const).map((v) => (
              <button key={v} onClick={() => setOnly(v)} className={`rounded-full px-3.5 py-1.5 ${only === v ? "bg-tile text-ink shadow-sm" : "text-ink-2 hover:text-ink"}`}>
                {v === "flagged" ? "Needs attention" : "All pending"}
              </button>
            ))}
          </div>
        }
      />
      <ErrorNote error={error} />
      <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi accent label="Pending" value={num(all.filter((r) => r.review_state === "PENDING_REVIEW").length)} />
        <Kpi label="Flagged & pending" value={num(all.filter((r) => r.review_state === "PENDING_REVIEW" && r.flags.length).length)} />
        <Kpi label="Reviewed" value={num(reviewed.length)} />
        <Kpi label="Overrides" value={num(reviewed.filter((r) => r.decision === "OVERRIDDEN").length)} />
      </div>

      <div className="flex flex-col gap-3">
        {pending.length ? pending.map((r) => <PendingCard key={r.id} row={r} source={source} onDone={reload} />) : <Empty>Nothing waiting for review.</Empty>}
      </div>

      {reviewed.length > 0 && (
        <Card title="Decision log" className="mt-4">
          <table className="num w-full text-[13px]">
            <thead>
              <tr className="border-b border-line text-left text-xs text-ink-2">
                {["Package", "Path", "Recommendation", "Decision", "Reviewer", "Decided", "Reason"].map((h) => (
                  <th key={h} className="py-1.5 pr-3 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {reviewed.map((r) => (
                <tr key={r.id} className="border-b border-line last:border-0">
                  <td className="py-1.5 pr-3 font-semibold">
                    <Link href={`/verifications/view?id=${r.id}`} className="hover:underline">
                      {r.package_id}
                    </Link>
                  </td>
                  <td className="py-1.5 pr-3">
                    <PathBadge path={r.path} />
                  </td>
                  <td className="py-1.5 pr-3">
                    <FlagChips recommendation={r.recommendation} flags={r.flags} />
                  </td>
                  <td className="py-1.5 pr-3">
                    <ReviewPill state={r.review_state} decision={r.decision} />
                  </td>
                  <td className="py-1.5 pr-3">{r.reviewer}</td>
                  <td className="py-1.5 pr-3 text-ink-2">{when(r.decided_at)}</td>
                  <td className="py-1.5 text-ink-2">{r.override_reason ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </>
  );
}

function PendingCard({ row, source, onDone }: { row: VerificationRow; source: string; onDone: () => void }) {
  const router = useRouter();
  const { data } = useApi<{ audit: Audit }>(`/api/verifications/${row.id}?source=${encodeURIComponent(source)}`);
  return (
    <Card>
      <div className="mb-2 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Link href={`/verifications/view?id=${row.id}`} className="text-[15px] font-semibold hover:underline">
              {row.package_id}
            </Link>
            <PathBadge path={row.path} />
            <span className="text-xs text-ink-2">{when(row.created_at)}</span>
          </div>
          <div className="mt-1">
            <FlagChips recommendation={row.recommendation} flags={row.flags} />
          </div>
        </div>
        <div className="text-right">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-2">Impact</div>
          <div className="num text-2xl font-semibold">{eur(row.impact_eur)}</div>
        </div>
      </div>
      {data ? (
        <Findings findings={data.audit.findings} onOpen={() => router.push(`/verifications/view?id=${row.id}`)} />
      ) : (
        <Spinner />
      )}
      <div className="mt-3">
        <DecisionForm id={row.id} source={source} onDone={onDone} />
      </div>
    </Card>
  );
}
