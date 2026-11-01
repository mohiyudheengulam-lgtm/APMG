"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, FileText } from "lucide-react";
import { Audit, useApi } from "@/lib/api";
import { num, secs, when } from "@/lib/format";
import { useSource } from "@/components/source";
import { Card, ErrorNote, FlagChips, Kpi, PageHeader, PathBadge, ReviewPill, Spinner } from "@/components/ui";
import { Findings, StepList, SubmittedValues, pdfUrl } from "@/components/evidence";
import { DecisionForm } from "@/components/decision";

type Detail = {
  row: { id: string; package_id: string; path: string; created_at: string; review_state: string };
  audit: Audit;
  expected: string | null;
};

const TABS = ["Tool calls", "Calculations", "Cited clauses", "Submitted values", "Run settings"] as const;

export default function VerificationDetail() {
  const { id } = useParams<{ id: string }>();
  const { source } = useSource();
  const { data, error, reload } = useApi<Detail>(`/api/verifications/${id}?source=${encodeURIComponent(source)}`);
  const [tab, setTab] = useState<(typeof TABS)[number]>("Tool calls");
  const [doc, setDoc] = useState<{ name: string; page: number } | null>(null);

  if (error) return <ErrorNote error={error} />;
  if (!data) return <Spinner label="Loading…" />;
  const { audit: a, row } = data;
  const pkg = a.package_id;
  const viewer = doc ?? (a.findings?.[0]?.evidence?.at(-1) ? { name: a.findings[0].evidence.at(-1)!.document, page: a.findings[0].evidence.at(-1)!.page } : null);
  const docs = Array.from(new Set([...Object.values(a.submitted_values ?? {}).map((d) => d.document), ...a.cited_clauses.map((c) => c.document)])).filter(
    (d) => d.endsWith(".pdf"),
  );

  return (
    <>
      <Link href="/verifications" className="mb-2 inline-flex items-center gap-1 text-xs text-ink-2 hover:text-ink">
        <ArrowLeft size={12} /> All verifications
      </Link>
      <PageHeader
        title={`${pkg} · verification ${a.verification_id}`}
        sub={`Created ${when(row.created_at)}`}
        right={
          <div className="flex items-center gap-2">
            <PathBadge path={a.retrieval_path} />
            <ReviewPill state={a.review_state} decision={a.manager_decision?.decision ?? null} />
          </div>
        }
      />
      <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Kpi accent label="Run status" value={<span className="text-xl">{a.run_status}</span>} sub={`${a.steps.length} of 10 steps`} />
        <Kpi label="Time" value={secs(a.seconds_total)} sub="wall-clock" />
        <Kpi label="Input tokens" value={num(a.prompt_tokens_total)} sub={`${num(a.output_tokens_total)} output`} />
        <Kpi label="Invalid tool calls" value={num(a.invalid_tool_calls)} sub="rejected by validation/guards" />
        <Kpi label="Ground truth" value={<span className="text-sm">{data.expected ? <FlagChips recommendation={data.expected} /> : "–"}</span>} sub="benchmark packages only" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-4">
          <Card title="Agent recommendation" right={<FlagChips recommendation={a.recommendation} />}>
            <Findings findings={a.findings} onOpen={(name, page) => setDoc({ name, page })} />
            <div className="mt-4">
              {a.manager_decision ? (
                <div className="rounded border border-line bg-[#faf9f8] p-3 text-sm">
                  <b>{a.manager_decision.decision}</b> by {a.manager_decision.reviewer} · {when(a.manager_decision.timestamp)}
                  {a.manager_decision.override_reason && <div className="text-ink-2">“{a.manager_decision.override_reason}”</div>}
                </div>
              ) : (
                <DecisionForm id={a.verification_id} source={source} onDone={reload} />
              )}
            </div>
          </Card>

          <Card>
            <div className="mb-3 flex flex-wrap gap-1 border-b border-line">
              {TABS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`-mb-px border-b-2 px-3 py-1.5 text-[13px] ${tab === t ? "border-accent font-semibold text-ink" : "border-transparent text-ink-2 hover:text-ink"}`}
                >
                  {t}
                </button>
              ))}
            </div>
            {tab === "Tool calls" && <StepList steps={a.steps} />}
            {tab === "Calculations" &&
              (a.calculations.length ? (
                <table className="num w-full text-[13px]">
                  <thead>
                    <tr className="border-b border-line text-left text-xs text-ink-2">
                      {["Flag", "Item", "Expected", "Actual", "Impact", "Formula"].map((h) => (
                        <th key={h} className="py-1.5 pr-3 font-semibold">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {a.calculations.map((c, i) => (
                      <tr key={i} className="border-b border-line last:border-0">
                        <td className="py-1.5 pr-3">{c.flag.replace("FLAGGED_", "")}</td>
                        <td className="py-1.5 pr-3">{c.item_no}</td>
                        <td className="py-1.5 pr-3">{c.expected}</td>
                        <td className="py-1.5 pr-3">{c.actual}</td>
                        <td className="py-1.5 pr-3">{c.amount}</td>
                        <td className="py-1.5 font-mono text-xs">{c.formula}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-sm text-ink-2">No differences computed by the deterministic tools.</p>
              ))}
            {tab === "Cited clauses" &&
              (a.cited_clauses.length ? (
                <ul className="flex flex-col gap-2 text-[13px]">
                  {a.cited_clauses.map((c, i) => (
                    <li key={i} className="rounded border border-line p-2">
                      <div className="flex items-center justify-between">
                        <b>{c.label}</b>
                        <span className={`text-xs font-semibold ${c.allowed ? "text-[#107c10]" : "text-[#a4262c]"}`}>{c.allowed ? "judged allowed" : "judged not allowed"}</span>
                      </div>
                      <button onClick={() => setDoc({ name: c.document, page: c.page })} className="text-xs text-[#2a78d6] hover:underline">
                        {c.document} · page {c.page}
                      </button>
                      <p className="mt-1 text-xs text-ink-2">{c.reason}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-ink-2">No MSA clause cited.</p>
              ))}
            {tab === "Submitted values" && <SubmittedValues audit={a} />}
            {tab === "Run settings" && <pre className="text-xs text-ink-2">{JSON.stringify(a.model_settings, null, 2)}</pre>}
          </Card>
        </div>

        <Card
          title="Source document"
          className="xl:sticky xl:top-16 xl:self-start"
          right={
            <div className="flex flex-wrap justify-end gap-1">
              {docs.map((d) => (
                <button
                  key={d}
                  onClick={() => setDoc({ name: d, page: 1 })}
                  className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[11px] ${viewer?.name === d ? "border-[#2a78d6] text-[#2a78d6]" : "border-line text-ink-2"}`}
                >
                  <FileText size={11} /> {d}
                </button>
              ))}
            </div>
          }
        >
          {viewer ? (
            <>
              <p className="mb-2 text-xs text-ink-2">
                {viewer.name} · page {viewer.page}
              </p>
              <iframe key={`${viewer.name}-${viewer.page}`} src={pdfUrl(pkg, viewer.name, viewer.page)} className="h-[72vh] w-full rounded border border-line bg-white" />
            </>
          ) : (
            <p className="text-sm text-ink-2">Click an evidence reference to open the cited page.</p>
          )}
        </Card>
      </div>
    </>
  );
}
