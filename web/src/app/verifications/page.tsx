"use client";

import Link from "next/link";
import { useState } from "react";
import { VerificationRow, useApi } from "@/lib/api";
import { eur, num, secs, when } from "@/lib/format";
import { useSource } from "@/components/source";
import { Card, Empty, ErrorNote, FlagChips, PageHeader, PathBadge, ReviewPill, Spinner } from "@/components/ui";

export default function VerificationsPage() {
  const { source } = useSource();
  const { data: rows, error, loading } = useApi<VerificationRow[]>(`/api/verifications?source=${encodeURIComponent(source)}`, 10000);
  const [path, setPath] = useState<"all" | "A" | "B">("all");
  const [state, setState] = useState<"all" | "flagged" | "pending">("all");
  const shown = (rows ?? []).filter(
    (r) => (path === "all" || r.path === path) && (state === "all" || (state === "flagged" ? r.flags.length > 0 : r.review_state === "PENDING_REVIEW")),
  );

  return (
    <>
      <PageHeader
        title="Evidence"
        sub="Every verification with its tool calls, retrieved evidence, calculations and citations."
        right={
          <div className="flex gap-2">
            <Seg value={path} set={setPath} options={[["all", "All paths"], ["A", "Path A"], ["B", "Path B"]]} />
            <Seg value={state} set={setState} options={[["all", "All"], ["flagged", "Flagged"], ["pending", "Pending"]]} />
          </div>
        }
      />
      <ErrorNote error={error} />
      <Card>
        {loading && !rows ? (
          <Spinner label="Loading…" />
        ) : !shown.length ? (
          <Empty>No verifications match.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="num w-full text-[13px]">
              <thead>
                <tr className="border-b border-line text-left text-xs text-ink-2">
                  {["Package", "Path", "Run", "Recommendation", "Impact", "Time", "Tokens", "Steps", "Invalid calls", "Created", "Review"].map((h) => (
                    <th key={h} className="py-2 pr-3 font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shown.map((r) => (
                  <tr key={r.id} className="border-b border-line last:border-0 hover:bg-[#faf9f8]">
                    <td className="py-2 pr-3 font-semibold">
                      <Link href={`/verifications/view?id=${r.id}`} className="text-[#2a78d6] hover:underline">
                        {r.package_id}
                      </Link>
                    </td>
                    <td className="py-2 pr-3">
                      <PathBadge path={r.path} />
                    </td>
                    <td className="py-2 pr-3 text-ink-2">{r.run ?? "–"}</td>
                    <td className="py-2 pr-3">
                      <FlagChips recommendation={r.recommendation} flags={r.flags} />
                    </td>
                    <td className="py-2 pr-3 text-right">{eur(r.impact_eur)}</td>
                    <td className="py-2 pr-3 text-right">{secs(r.seconds)}</td>
                    <td className="py-2 pr-3 text-right">{num(r.prompt_tokens)}</td>
                    <td className="py-2 pr-3 text-right">{r.steps}</td>
                    <td className={`py-2 pr-3 text-right ${r.invalid_tool_calls ? "text-[#a4262c]" : ""}`}>{r.invalid_tool_calls ?? "–"}</td>
                    <td className="py-2 pr-3 text-ink-2">{when(r.created_at)}</td>
                    <td className="py-2">
                      <ReviewPill state={r.review_state} decision={r.decision} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}

function Seg<T extends string>({ value, set, options }: { value: T; set: (v: T) => void; options: [T, string][] }) {
  return (
    <div className="inline-flex overflow-hidden rounded border border-line bg-white text-xs">
      {options.map(([v, l]) => (
        <button key={v} onClick={() => set(v)} className={`px-2.5 py-1.5 ${value === v ? "bg-[#252423] text-white" : "text-ink-2 hover:bg-[#faf9f8]"}`}>
          {l}
        </button>
      ))}
    </div>
  );
}
