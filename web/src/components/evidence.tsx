"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, FileText, Wrench } from "lucide-react";
import { Audit, FLAG_LABEL, Finding, Step } from "@/lib/api";
import { eur, num, secs } from "@/lib/format";

export function pdfUrl(pkg: string, doc: string, page?: number) {
  return `/api/packages/${encodeURIComponent(pkg)}/files/${encodeURIComponent(doc)}${page ? `#page=${page}` : ""}`;
}

export function Findings({ findings, onOpen }: { findings: Finding[] | null; onOpen?: (doc: string, page: number) => void }) {
  if (!findings?.length) return <p className="text-sm text-ink-2">No discrepancies in the recommendation.</p>;
  return (
    <ul className="flex flex-col gap-2">
      {findings.map((f, i) => (
        <li key={i} className="rounded-sm border-l-[3px] border-bad bg-bad-soft px-3 py-2 text-[13px]">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <span className="font-semibold text-ink">
              {FLAG_LABEL[f.flag] ?? f.flag}
              {f.item_no ? <span className="font-normal text-ink-2"> · item {f.item_no}</span> : null}
            </span>
            {f.amount ? <span className="num font-semibold text-bad">{eur(f.amount, 2)}</span> : null}
          </div>
          {(f.expected || f.actual) && (
            <div className="num text-ink-2">
              expected <b className="text-ink">{f.expected ?? "–"}</b> · invoiced <b className="text-ink">{f.actual ?? "–"}</b>
            </div>
          )}
          {f.formula && <div className="font-mono text-xs text-ink-2">{f.formula}</div>}
          <div className="mt-1 flex flex-wrap gap-1.5">
            {f.evidence.map((e, j) => (
              <button
                key={j}
                onClick={() => onOpen?.(e.document, e.page)}
                className="inline-flex items-center gap-1 rounded-xl border border-line bg-white px-1.5 py-0.5 text-xs text-ink-2 hover:border-primary-deep hover:text-link"
                title="Open source document at this page"
              >
                <FileText size={12} /> {e.document} · p.{e.page}
              </button>
            ))}
          </div>
        </li>
      ))}
    </ul>
  );
}

function StepRow({ s, live }: { s: Step; live?: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="border-b border-line last:border-0">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-3 px-2 py-2 text-left text-[13px] hover:bg-surface">
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="w-14 shrink-0 font-semibold text-ink">Step {s.step}</span>
        <span className="flex flex-1 flex-wrap gap-1">
          {s.tool_calls.length ? (
            s.tool_calls.map((c, i) => {
              const bad = c.result.startsWith("Error");
              return (
                <span
                  key={i}
                  className={`inline-flex items-center gap-1 rounded-xl px-1.5 py-0.5 font-mono text-[11px] ${
                    bad ? "bg-bad-soft text-bad" : "bg-surface-2 text-ink"
                  }`}
                >
                  <Wrench size={10} /> {c.name}
                </span>
              );
            })
          ) : (
            <span className="text-xs text-muted">no tool call</span>
          )}
        </span>
        <span className="num shrink-0 text-xs text-ink-2">
          {secs(s.seconds)} · {num(s.prompt_tokens)} tok
        </span>
      </button>
      {open && (
        <div className={`space-y-2 px-8 pb-3 ${live ? "" : ""}`}>
          {s.tool_calls.map((c, i) => (
            <div key={i} className="rounded-xl border border-line">
              <div className="border-b border-line bg-surface px-2 py-1 font-mono text-xs font-semibold">{c.name}</div>
              {Object.keys(c.arguments ?? {}).length > 0 && (
                <pre className="max-h-48 overflow-auto border-b border-line px-2 py-1.5 text-[11px] whitespace-pre-wrap text-ink-2">
                  {JSON.stringify(c.arguments, null, 1)}
                </pre>
              )}
              <pre className={`max-h-72 overflow-auto px-2 py-1.5 text-[11px] whitespace-pre-wrap ${c.result.startsWith("Error") ? "text-bad" : "text-ink"}`}>
                {c.result}
              </pre>
            </div>
          ))}
          {!s.tool_calls.length && s.content && <p className="text-xs text-ink-2">{s.content}</p>}
        </div>
      )}
    </li>
  );
}

export function StepList({ steps, live }: { steps: Step[]; live?: boolean }) {
  if (!steps.length) return <p className="text-sm text-ink-2">No steps yet.</p>;
  return (
    <ol className="rounded-xl border border-line">
      {steps.map((s) => (
        <StepRow key={s.step} s={s} live={live} />
      ))}
    </ol>
  );
}

export function SubmittedValues({ audit }: { audit: Audit }) {
  const docs = Object.entries(audit.submitted_values ?? {});
  if (!docs.length) return <p className="text-sm text-ink-2">The agent submitted no values.</p>;
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {docs.map(([type, d]) => (
        <div key={type} className="rounded-xl border border-line">
          <div className="border-b border-line bg-surface px-2 py-1 text-xs font-semibold">
            {type.replace("_", " ")} <span className="font-normal text-ink-2">· {d.document}</span>
          </div>
          <table className="num w-full text-xs">
            <thead className="text-ink-2">
              <tr>
                <th className="px-2 py-1 text-left font-normal">Item</th>
                <th className="px-2 py-1 text-right font-normal">Qty</th>
                <th className="px-2 py-1 text-right font-normal">Price</th>
                <th className="px-2 py-1 text-right font-normal">Total</th>
              </tr>
            </thead>
            <tbody>
              {d.lines.map((l, i) => (
                <tr key={i} className="border-t border-line">
                  <td className="px-2 py-1">{l.item_no}</td>
                  <td className="px-2 py-1 text-right">{l.quantity}</td>
                  <td className="px-2 py-1 text-right">{l.unit_price ?? "–"}</td>
                  <td className="px-2 py-1 text-right">{l.line_total ?? "–"}</td>
                </tr>
              ))}
              {d.surcharges?.map((s, i) => (
                <tr key={`s${i}`} className="border-t border-line text-bad">
                  <td className="px-2 py-1" colSpan={3}>
                    {s.label}
                  </td>
                  <td className="px-2 py-1 text-right">{s.amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
