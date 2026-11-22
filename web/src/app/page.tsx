"use client";

import Link from "next/link";
import { FLAG_LABEL, Overview, VerificationRow, useApi } from "@/lib/api";
import { eur, num, secs, when } from "@/lib/format";
import { useSource } from "@/components/source";
import { Card, Empty, ErrorNote, FlagChips, Kpi, PageHeader, PathBadge, ReviewPill, Spinner } from "@/components/ui";
import { ColumnBars, HBar } from "@/components/charts";

export default function OverviewPage() {
  const { source } = useSource();
  const q = `source=${encodeURIComponent(source)}`;
  const { data: o, error, loading } = useApi<Overview>(`/api/overview?${q}`, 10000);
  const { data: rows } = useApi<VerificationRow[]>(`/api/verifications?${q}`, 10000);

  if (loading && !o) return <Spinner label="Loading…" />;
  const pending = (rows ?? []).filter((r) => r.review_state === "PENDING_REVIEW").sort((a, b) => Number(b.flags.length > 0) - Number(a.flags.length > 0) || b.impact_eur - a.impact_eur);
  const byPkg = Object.values(
    (rows ?? []).reduce<Record<string, { name: string; value: number }>>((acc, r) => {
      acc[r.package_id] = { name: r.package_id, value: Math.max(acc[r.package_id]?.value ?? 0, r.impact_eur) };
      return acc;
    }, {}),
  )
    .filter((d) => d.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  return (
    <>
      <PageHeader title="Verification overview" sub="Invoices checked by the agent and their review status." />
      <ErrorNote error={error} />
      {!o ? null : o.total === 0 ? (
        <Empty>
          No verifications in this data source yet. <Link href="/verify" className="text-link underline">Run one</Link> or pick a benchmark result set
          in the top bar.
        </Empty>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Kpi accent label="Verifications" value={num(o.total)} sub={`${o.packages} packages · A ${o.by_path.A ?? 0} / B ${o.by_path.B ?? 0}`} />
            <Kpi label="Pending review" value={num(o.pending)} sub={`${o.pending_flagged} flagged`} />
            <Kpi label="Flagged" value={num(o.flagged)} sub={`${o.clean} clean · ${o.no_result} without result`} />
            <Kpi label="Discrepancy value" value={eur(o.impact_eur)} sub="sum of flagged amounts" />
            <Kpi label="Median time" value={secs(o.median_seconds)} sub="per verification" />
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card title="Discrepancies by type">
              {Object.keys(o.flags).length ? (
                <HBar data={Object.entries(o.flags).map(([k, v]) => ({ name: FLAG_LABEL[k] ?? k, value: v }))} />
              ) : (
                <Empty>No flags raised.</Empty>
              )}
            </Card>
            <Card title="Discrepancy value by package">
              {byPkg.length ? <HBar data={byPkg} format={(v) => eur(v)} /> : <Empty>No monetary discrepancies.</Empty>}
            </Card>
            <Card title="Outcome & review status">
              <ColumnBars
                data={[
                  { name: "Clean", value: o.clean, color: "#1e7a3c" },
                  { name: "Flagged", value: o.flagged, color: "#c0302a" },
                  { name: "No result", value: o.no_result, color: "#d9a21b" },
                  { name: "Reviewed", value: o.reviewed, color: "#8c8f88" },
                ]}
                height={220}
              />
            </Card>
          </div>

          <Card title="Awaiting manager review" right={<Link href="/approvals" className="text-xs font-semibold text-link hover:underline">Open approvals →</Link>}>
            {pending.length ? (
              <div className="overflow-x-auto">
                <table className="num w-full text-[13px]">
                  <thead>
                    <tr className="border-b border-line text-left text-xs text-ink-2">
                      <th className="py-2 pr-3 font-semibold">Package</th>
                      <th className="py-2 pr-3 font-semibold">Path</th>
                      <th className="py-2 pr-3 font-semibold">Recommendation</th>
                      <th className="py-2 pr-3 text-right font-semibold">Impact</th>
                      <th className="w-40 py-2 pr-3 font-semibold" />
                      <th className="py-2 pr-3 text-right font-semibold">Time</th>
                      <th className="py-2 pr-3 font-semibold">Created</th>
                      <th className="py-2 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pending.slice(0, 12).map((r) => {
                      const max = Math.max(...pending.map((p) => p.impact_eur), 1);
                      return (
                        <tr key={r.id} className="border-b border-line last:border-0 hover:bg-surface">
                          <td className="py-2 pr-3 font-semibold">
                            <Link href={`/verifications/view?id=${r.id}`} className="hover:underline">
                              {r.package_id}
                            </Link>
                          </td>
                          <td className="py-2 pr-3">
                            <PathBadge path={r.path} />
                          </td>
                          <td className="py-2 pr-3">
                            <FlagChips recommendation={r.recommendation} flags={r.flags} />
                          </td>
                          <td className="py-2 pr-3 text-right">{eur(r.impact_eur)}</td>
                          <td className="py-2 pr-3">
                            <div className="h-2 rounded-full bg-surface-2">
                              <div className="h-2 rounded-full bg-primary" style={{ width: `${(r.impact_eur / max) * 100}%` }} />
                            </div>
                          </td>
                          <td className="py-2 pr-3 text-right text-ink-2">{secs(r.seconds)}</td>
                          <td className="py-2 pr-3 text-ink-2">{when(r.created_at)}</td>
                          <td className="py-2">
                            <ReviewPill state={r.review_state} decision={r.decision} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty>Nothing pending — all verifications are reviewed.</Empty>
            )}
          </Card>
        </div>
      )}
    </>
  );
}
