"use client";

import { useCallback, useEffect, useState } from "react";

export type Flag =
  | "FLAGGED_PRICE_MISMATCH"
  | "FLAGGED_QUANTITY_MISMATCH"
  | "FLAGGED_LINE_TOTAL_MISMATCH"
  | "FLAGGED_SURCHARGE"
  | "FLAGGED_MISSING_DOCUMENT";

export const FLAG_LABEL: Record<string, string> = {
  FLAGGED_PRICE_MISMATCH: "Price",
  FLAGGED_QUANTITY_MISMATCH: "Quantity",
  FLAGGED_LINE_TOTAL_MISMATCH: "Line total",
  FLAGGED_SURCHARGE: "Surcharge",
  FLAGGED_MISSING_DOCUMENT: "Missing document",
};

export type Source = { id: string; label: string };

export type VerificationRow = {
  id: string;
  package_id: string;
  path: "A" | "B";
  created_at: string;
  run_status: string;
  recommendation: string | null;
  flags: string[];
  review_state: "PENDING_REVIEW" | "REVIEWED";
  decision: "APPROVED" | "REJECTED" | "OVERRIDDEN" | null;
  reviewer: string | null;
  decided_at: string | null;
  override_reason: string | null;
  impact_eur: number;
  seconds: number | null;
  prompt_tokens: number | null;
  steps: number;
  invalid_tool_calls: number | null;
  run: number | null;
};

export type Overview = {
  total: number;
  packages: number;
  pending: number;
  pending_flagged: number;
  flagged: number;
  no_result: number;
  clean: number;
  reviewed: number;
  overrides: number;
  impact_eur: number;
  median_seconds: number | null;
  flags: Record<string, number>;
  by_path: Record<string, number>;
  by_day: Record<string, number>;
};

export type ToolCall = { name: string; arguments: Record<string, unknown>; result: string };
export type Step = {
  step: number;
  tool_calls: ToolCall[];
  prompt_tokens: number;
  output_tokens: number;
  seconds: number;
  content: string;
};
export type Evidence = { document: string; page: number };
export type Finding = {
  flag: string;
  item_no: string | null;
  expected: string | null;
  actual: string | null;
  amount: string | null;
  formula: string | null;
  evidence: Evidence[];
};

export type Audit = {
  verification_id: string;
  package_id: string;
  retrieval_path: "A" | "B";
  model_settings: Record<string, unknown>;
  run_status: string;
  seconds_total: number;
  prompt_tokens_total: number;
  output_tokens_total: number;
  steps: Step[];
  invalid_tool_calls: number;
  submitted_values: Record<string, { document: string; lines: Record<string, string>[]; surcharges?: { label: string; amount: string }[] }>;
  calculations: Finding[];
  cited_clauses: { label: string; document: string; page: number; allowed: boolean; reason: string }[];
  recommendation: string | null;
  findings: Finding[] | null;
  review_state: string;
  manager_decision: { decision: string; reviewer: string; timestamp: string; override_reason: string | null } | null;
};

export type Package = {
  id: string;
  kind: "benchmark" | "upload";
  files: string[];
  case_type: string | null;
  vendor: string | null;
  expected: string | null;
  indexed: Record<"A" | "B", boolean>;
};

export type Job = {
  id: string;
  package: string;
  path: "A" | "B";
  status: "queued" | "running" | "done" | "error";
  stage: string;
  steps: Step[];
  verification_id?: string;
  recommendation?: string | null;
  run_status?: string;
  error?: string;
  created_at: string;
};

export async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { cache: "no-store", ...init });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

/** Fetch + optional polling. `url` null skips. */
export function useApi<T>(url: string | null, pollMs?: number) {
  const [state, setState] = useState<{ url: string | null; data?: T; error?: string }>({ url: null });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!url) return;
    let alive = true;
    const load = () =>
      api<T>(url).then(
        (data) => alive && setState({ url, data }),
        (e) => alive && setState((s) => ({ url, data: s.url === url ? s.data : undefined, error: e instanceof Error ? e.message : String(e) })),
      );
    load();
    const t = pollMs ? setInterval(load, pollMs) : undefined;
    return () => {
      alive = false;
      if (t) clearInterval(t);
    };
  }, [url, pollMs, tick]);

  const current = state.url === url;
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return {
    data: current ? state.data : undefined,
    error: current ? state.error : undefined,
    loading: !!url && (!current || (state.data === undefined && state.error === undefined)),
    reload,
  };
}
