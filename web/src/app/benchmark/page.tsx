"use client";

import { useState } from "react";
import { FLAG_LABEL, useApi } from "@/lib/api";
import { num, pct } from "@/lib/format";
import { Card, Empty, ErrorNote, Kpi, PageHeader, Spinner } from "@/components/ui";
import { PathBars } from "@/components/charts";

type PathSummary = {
  runs: number;
  field_em: number;
  calc_em: number;
  citation_acc: number;
  recommendation_acc: number;
  flags: Record<string, [number, number, number]>;
  flag_micro: [number, number, number];
  latency_median_s: number;
  prompt_tokens_mean: number;
  tokens_per_correct_field: number;
  valid_share: number;
  invalid_tool_call_rate: number;
  step_limit_share: number;
  evidence_complete_share: number;
  prep_build_s_total: number;
  prep_extract_s_total: number;
  prep_storage_bytes: number;
  by_case: Record<string, number>;
  causes: Record<string, number>;
};
type Summary = { A?: PathSummary; B?: PathSummary; _governance: { decisions_without_signoff: number }; _routing: Record<string, { path: string; reason: string }> };
type Bench = { summary: Summary; runs: Record<string, string>[]; manifest: Record<string, unknown> };

const PATHS = ["A", "B"] as const;

export default function BenchmarkPage() {
  const { data: tags, error } = useApi<string[]>("/api/benchmarks");
  const [picked, setTag] = useState<string>();
  const tag = picked ?? tags?.at(-1);
  const { data: b } = useApi<Bench>(tag ? `/api/benchmarks/${tag}` : null);

  const s = b?.summary;
  const both = (k: keyof PathSummary, f: (v: number) => string) =>
    PATHS.filter((p) => s?.[p]).map((p) => (
      <span key={p} className="mr-3">
        <span className="text-xs font-semibold" style={{ color: p === "A" ? "var(--series-a)" : "var(--series-b)" }}>
          {p}
        </span>{" "}
        {f(s![p]![k] as number)}
      </span>
    ));
  const metric = (name: string, k: keyof PathSummary) => ({ name, A: s?.A?.[k] as number | undefined, B: s?.B?.[k] as number | undefined });

  return (
    <>
      <PageHeader
        title="Benchmark · Path A vs Path B"
        sub="Controlled comparison on the generated corpus (Exposé §6). Small corpus — descriptive only."
        right={
          tags?.length ? (
            <select value={tag} onChange={(e) => setTag(e.target.value)} className="rounded-xl border border-line bg-white px-2 py-1.5 text-sm">
              {tags.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          ) : null
        }
      />
      <ErrorNote error={error} />
      {!tags ? (
        <Spinner label="Loading…" />
      ) : !tags.length ? (
        <Empty>
          No evaluated result set yet. Run <code>scripts/run_benchmark.py</code>, then <code>scripts/evaluate.py --tag &lt;tag&gt;</code>.
        </Empty>
      ) : !s ? (
        <Spinner label="Loading…" />
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Kpi accent label="Field accuracy (EM)" value={<span className="text-xl">{both("field_em", (v) => pct(v))}</span>} sub="extracted values" />
            <Kpi label="Flag F1 (micro)" value={<span className="text-xl">{both("flag_micro", (v) => num((v as unknown as number[])[2], 2))}</span>} sub="all flag types" />
            <Kpi label="Median latency" value={<span className="text-xl">{both("latency_median_s", (v) => `${num(v)} s`)}</span>} sub="per verification" />
            <Kpi label="Input tokens" value={<span className="text-xl">{both("prompt_tokens_mean", (v) => `${num(v / 1000, 1)}k`)}</span>} sub="mean per verification" />
            <Kpi label="Unsigned decisions" value={s._governance.decisions_without_signoff} sub="expected 0" />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="1 · Accuracy (%)">
              <PathBars
                domain={[0, 100]}
                format={(v) => `${num(v)}`}
                data={[metric("Field EM", "field_em"), metric("Calc EM", "calc_em"), metric("Citation", "citation_acc"), metric("Recommendation", "recommendation_acc")]}
              />
            </Card>
            <Card title="1 · Flag detection F1 by type">
              <PathBars
                domain={[0, 1]}
                format={(v) => num(v, 1)}
                data={Object.keys(FLAG_LABEL).map((f) => ({ name: FLAG_LABEL[f], A: s.A?.flags[f]?.[2], B: s.B?.flags[f]?.[2] }))}
              />
            </Card>
            <Card title="2 · Median latency (s)">
              <PathBars height={200} format={(v) => num(v)} data={[metric("Seconds per verification", "latency_median_s")]} />
            </Card>
            <Card title="3 · Input tokens per verification">
              <PathBars height={200} format={(v) => `${num(v / 1000, 1)}k`} data={[metric("Mean input tokens", "prompt_tokens_mean"), metric("Per correct field", "tokens_per_correct_field")]} />
            </Card>
            <Card title="5 · Reliability & governance (%)">
              <PathBars
                domain={[0, 100]}
                format={(v) => num(v)}
                data={[metric("Valid output", "valid_share"), metric("Evidence complete", "evidence_complete_share"), metric("Invalid calls", "invalid_tool_call_rate"), metric("Step limit", "step_limit_share")]}
              />
            </Card>
            <Card title="Correct recommendation by case type (%)">
              <PathBars
                domain={[0, 100]}
                format={(v) => num(v)}
                data={Array.from(new Set(PATHS.flatMap((p) => Object.keys(s[p]?.by_case ?? {})))).map((c) => ({
                  name: c.replaceAll("_", " "),
                  A: s.A?.by_case[c],
                  B: s.B?.by_case[c],
                }))}
              />
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card title="4 · Preparation effort">
              <table className="num w-full text-[13px]">
                <thead>
                  <tr className="border-b border-line text-left text-xs text-ink-2">
                    <th className="py-1.5 font-semibold" />
                    {PATHS.map((p) => (
                      <th key={p} className="py-1.5 text-right font-semibold">
                        Path {p}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(
                    [
                      ["Build time, all packages (s)", (x: PathSummary) => num(x.prep_build_s_total, 1)],
                      ["of which extraction (s)", (x: PathSummary) => num(x.prep_extract_s_total, 1)],
                      ["Storage (KB)", (x: PathSummary) => num(x.prep_storage_bytes / 1024)],
                    ] as const
                  ).map(([l, f]) => (
                    <tr key={l} className="border-b border-line last:border-0">
                      <td className="py-1.5 text-ink-2">{l}</td>
                      {PATHS.map((p) => (
                        <td key={p} className="py-1.5 text-right">
                          {s[p] ? f(s[p]!) : "–"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-xs text-ink-2">Engineering hours: from the sprint log.</p>
            </Card>
            <Card title="SQ3 · Retrieval-path assignment">
              {Object.keys(s._routing ?? {}).length ? (
                <ul className="flex flex-col gap-2 text-[13px]">
                  {Object.entries(s._routing).map(([g, r]) => (
                    <li key={g} className="rounded-xl border border-line p-2">
                      <div className="font-semibold">{g}</div>
                      <div>
                        → Path <b style={{ color: r.path === "A" ? "var(--series-a)" : "var(--series-b)" }}>{r.path}</b>
                      </div>
                      <div className="text-xs text-ink-2">{r.reason}</div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-ink-2">Needs results for both paths.</p>
              )}
            </Card>
            <Card title="Error causes (first pass)">
              {PATHS.filter((p) => s[p]).map((p) => (
                <div key={p} className="mb-2 text-[13px]">
                  <b>Path {p}</b>:{" "}
                  {Object.entries(s[p]!.causes).length
                    ? Object.entries(s[p]!.causes)
                        .map(([k, v]) => `${k} ${v}`)
                        .join(" · ")
                    : "none"}
                </div>
              ))}
            </Card>
          </div>

          <Card title={`All runs (${b!.runs.length})`}>
            <div className="max-h-[420px] overflow-auto">
              <table className="num w-full text-[12px]">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-line text-left text-ink-2">
                    {Object.keys(b!.runs[0] ?? {}).map((h) => (
                      <th key={h} className="py-1.5 pr-3 font-semibold">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {b!.runs.map((r, i) => (
                    <tr key={i} className={`border-b border-line last:border-0 ${r.correct === "False" ? "bg-bad-soft" : ""}`}>
                      {Object.values(r).map((v, j) => (
                        <td key={j} className="py-1 pr-3">
                          {v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
