"use client";

import Link from "next/link";
import { useMemo, useRef, useState } from "react";
import { CheckCircle2, FileText, Layers, Play, Search, Upload, XCircle, Zap } from "lucide-react";
import { Job, Package, api, useApi } from "@/lib/api";
import { num, secs } from "@/lib/format";
import { Card, Empty, ErrorNote, FlagChips, PageHeader, PathBadge, Spinner } from "@/components/ui";
import { StepList, pdfUrl } from "@/components/evidence";

export default function VerifyPage() {
  const { data: pkgs, error, reload } = useApi<Package[]>("/api/packages");
  const [selected, setSelected] = useState<string | null>(null);
  const [path, setPath] = useState<"A" | "B">("A");
  const [assisted, setAssisted] = useState(false);
  const [filter, setFilter] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string>();
  const { data: job } = useApi<Job>(jobId ? `/api/jobs/${jobId}` : null, 2000);
  const { data: jobs } = useApi<Job[]>("/api/jobs", 5000);

  const pkg = pkgs?.find((p) => p.id === selected) ?? pkgs?.[0];
  const shown = useMemo(
    () => (pkgs ?? []).filter((p) => !filter || `${p.id} ${p.case_type ?? ""} ${p.vendor ?? ""}`.toLowerCase().includes(filter.toLowerCase())),
    [pkgs, filter],
  );
  const busy = job && (job.status === "queued" || job.status === "running");

  async function run() {
    if (!pkg) return;
    setRunError(undefined);
    try {
      const j = await api<Job>("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ package: pkg.id, path, assisted }),
      });
      setJobId(j.id);
    } catch (e) {
      setRunError(String(e instanceof Error ? e.message : e));
    }
  }

  return (
    <>
      <PageHeader title="Verify a package" sub="Pick a procurement package and retrieval path. The agent prepares a recommendation; a manager decides." />
      <ErrorNote error={error ?? runError} />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="flex flex-col gap-4">
          <Card title="Packages" right={<span className="text-xs text-ink-2">{pkgs?.length ?? 0} available</span>}>
            <div className="mb-2 flex items-center gap-2 rounded border border-line px-2">
              <Search size={14} className="text-muted" />
              <input
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter by id, case or vendor"
                className="w-full py-1.5 text-sm outline-none"
              />
            </div>
            <ul className="max-h-[420px] overflow-auto pr-1">
              {shown.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => setSelected(p.id)}
                    className={`mb-1 flex w-full items-center justify-between gap-2 rounded border px-3 py-2 text-left text-[13px] ${
                      pkg?.id === p.id ? "border-[#2a78d6] bg-[#eff6fc]" : "border-transparent hover:bg-[#faf9f8]"
                    }`}
                  >
                    <span>
                      <span className="font-semibold">{p.id}</span>
                      <span className="ml-2 text-xs text-ink-2">
                        {p.kind === "upload" ? "uploaded" : `${p.vendor} · ${p.case_type?.replaceAll("_", " ")}`}
                      </span>
                    </span>
                    <span className="flex items-center gap-1 text-[10px] text-ink-2">
                      <span
                        title={p.extraction?.status === "verified" ? "extraction verified against the documents' own totals" : p.extraction?.problems.join("\n")}
                        className={p.extraction?.status === "verified" ? "text-[#107c10]" : "font-bold text-[#8a6d00]"}
                      >
                        {p.extraction?.status === "verified" ? "✓" : "⚠"}
                      </span>
                      {(["A", "B"] as const).map((x) => (
                        <span key={x} className={`rounded px-1 ${p.indexed[x] ? "bg-[#edebe9]" : "text-muted"}`} title={p.indexed[x] ? "index built" : "not indexed yet"}>
                          {x}
                        </span>
                      ))}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Card>
          <BatchCard packages={shown.map((p) => p.id)} assisted={assisted} />
          <UploadCard onDone={(id) => (reload(), setSelected(id))} />
        </div>

        <div className="flex flex-col gap-4">
          <Card title={pkg ? `Run verification · ${pkg.id}` : "Run verification"}>
            {!pkg ? (
              <Empty>No packages yet.</Empty>
            ) : (
              <>
                <div className="mb-3 flex flex-wrap gap-1.5">
                  {pkg.files.map((f) => (
                    <a
                      key={f}
                      href={pdfUrl(pkg.id, f)}
                      target="_blank"
                      className="inline-flex items-center gap-1 rounded border border-line px-2 py-1 text-xs text-ink-2 hover:border-[#2a78d6] hover:text-[#2a78d6]"
                    >
                      <FileText size={12} /> {f}
                    </a>
                  ))}
                </div>
                <div className="mb-3 rounded border border-line bg-[#faf9f8] px-3 py-2 text-xs text-ink-2">
                  <span className="font-semibold text-ink">From the contract library: </span>
                  {pkg.contracts.length ? (
                    pkg.contracts.map((c) => (
                      <a key={c.id} href={pdfUrl(pkg.id, c.filename)} target="_blank" className="mr-2 inline-flex items-center gap-1 text-[#2a78d6] hover:underline">
                        <FileText size={11} /> {c.filename} ({c.kind === "msa" ? `MSA ${c.number ?? ""}` : "guideline"})
                      </a>
                    ))
                  ) : (
                    <span className="text-[#a4262c]">
                      no contract linked — add the supplier&apos;s MSA under <Link href="/contracts" className="underline">Contracts</Link>
                    </span>
                  )}
                </div>
                <div
                  className={`mb-3 rounded border px-3 py-2 text-xs ${
                    pkg.extraction?.status === "verified" ? "border-[#c6e7c6] bg-[#f1faf1] text-[#107c10]" : "border-[#f2d38a] bg-[#fff8e1] text-[#8a6d00]"
                  }`}
                >
                  {pkg.extraction?.status === "verified" ? (
                    <b>✓ Extraction verified — the extracted lines reproduce the documents&apos; own totals.</b>
                  ) : (
                    <>
                      <b>⚠ Extraction uncertain</b> — assisted mode is not available for this package:
                      <ul className="mt-1 list-disc pl-5">
                        {pkg.extraction?.problems.map((x) => <li key={x}>{x}</li>)}
                      </ul>
                    </>
                  )}
                </div>
                {pkg.expected && (
                  <p className="mb-3 text-xs text-ink-2">
                    Ground truth (benchmark): <FlagChips recommendation={pkg.expected} />
                  </p>
                )}
                <div className="mb-4 grid grid-cols-2 gap-2">
                  {(["A", "B"] as const).map((x) => (
                    <button
                      key={x}
                      onClick={() => setPath(x)}
                      className={`rounded border px-3 py-2.5 text-left ${path === x ? "border-[#2a78d6] bg-[#eff6fc]" : "border-line hover:bg-[#faf9f8]"}`}
                    >
                      <PathBadge path={x} />
                      <div className="mt-1 text-xs text-ink-2">
                        {x === "A" ? "500-token chunks · nomic-embed-text · FAISS top-5" : "OKF v0.2 concept files · index.md navigation"}
                      </div>
                    </button>
                  ))}
                </div>
                <label className="mb-3 flex cursor-pointer items-start gap-2 rounded border border-line px-3 py-2 text-xs text-ink-2">
                  <input type="checkbox" checked={assisted} onChange={(e) => setAssisted(e.target.checked)} className="mt-0.5" />
                  <span>
                    <span className="inline-flex items-center gap-1 font-semibold text-ink">
                      <Zap size={12} /> Assisted mode (fast)
                    </span>{" "}
                    — invoice, PO and goods receipt are pre-filled from extraction; the agent only checks the contract.
                    Only for packages whose extraction is verified (otherwise it runs in research mode). For real use only:
                    not part of the research comparison.
                  </span>
                </label>
                <button
                  onClick={run}
                  disabled={!!busy}
                  className="inline-flex w-full items-center justify-center gap-2 rounded bg-[#2a78d6] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#256abf] disabled:opacity-50"
                >
                  <Play size={16} /> {busy ? "Verification running…" : "Run verification"}
                </button>
                <p className="mt-2 text-xs text-ink-2">Runs locally on CPU — expect 2–4 minutes. Verifications are queued and run one at a time.</p>
              </>
            )}
          </Card>

          {job && <LiveJob job={job} />}

          {!!jobs?.length && (
            <Card title="Recent runs this session">
              <ul className="text-[13px]">
                {jobs.map((j) => (
                  <li key={j.id} className="flex items-center justify-between gap-2 border-b border-line py-1.5 last:border-0">
                    <span className="flex items-center gap-2">
                      <span className="font-semibold">{j.package}</span> <PathBadge path={j.path} />
                      {j.assisted && <span className="rounded bg-[#fff4ce] px-1.5 text-[10px] font-semibold text-[#8a6d00]">assisted</span>}
                    </span>
                    <span className="flex items-center gap-2">
                      {j.status === "done" ? <FlagChips recommendation={j.recommendation ?? null} /> : <span className="text-xs text-ink-2">{j.stage}</span>}
                      {j.verification_id && (
                        <Link href={`/verifications/view?id=${j.verification_id}`} className="text-xs font-semibold text-[#2a78d6] hover:underline">
                          Evidence
                        </Link>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function LiveJob({ job }: { job: Job }) {
  const tokens = job.steps.reduce((s, x) => s + x.prompt_tokens, 0);
  const seconds = job.steps.reduce((s, x) => s + x.seconds, 0);
  return (
    <Card
      title={`Verification progress · ${job.package}`}
      right={
        job.status === "done" ? (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#107c10]">
            <CheckCircle2 size={14} /> Saved as PENDING_REVIEW
          </span>
        ) : job.status === "error" ? (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#a4262c]">
            <XCircle size={14} /> Failed
          </span>
        ) : (
          <Spinner label={job.stage} />
        )
      }
    >
      <div className="mb-3 grid grid-cols-3 gap-2 text-center">
        {[
          ["Step", `${job.steps.length} / 10`],
          ["Agent time", secs(seconds)],
          ["Input tokens", num(tokens)],
        ].map(([l, v]) => (
          <div key={l} className="rounded bg-[#faf9f8] py-2">
            <div className="text-[11px] uppercase tracking-wider text-ink-2">{l}</div>
            <div className="num text-lg font-semibold">{v}</div>
          </div>
        ))}
      </div>
      <div className="mb-3 h-1.5 rounded-full bg-[#edebe9]">
        <div
          className={`h-1.5 rounded-full transition-all ${job.status === "error" ? "bg-[#d13438]" : "bg-[#2a78d6]"}`}
          style={{ width: `${job.status === "done" ? 100 : Math.min(job.steps.length * 10, 95)}%` }}
        />
      </div>
      {job.error && <p className="mb-2 text-sm text-[#a4262c]">{job.error}</p>}
      <StepList steps={job.steps} live />
      {job.status === "done" && (
        <div className="mt-3 flex items-center justify-between gap-2 rounded bg-[#faf9f8] px-3 py-2">
          <FlagChips recommendation={job.recommendation ?? null} />
          <Link href={`/verifications/view?id=${job.verification_id}`} className="text-sm font-semibold text-[#2a78d6] hover:underline">
            Open evidence →
          </Link>
        </div>
      )}
    </Card>
  );
}

function BatchCard({ packages, assisted }: { packages: string[]; assisted: boolean }) {
  const [paths, setPaths] = useState<("A" | "B")[]>(["A", "B"]);
  const [msg, setMsg] = useState<string>();
  const { data: q } = useApi<Record<string, number>>("/api/queue", 5000);
  async function queue() {
    try {
      const jobs = await api<Job[]>("/api/jobs/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ packages, paths, assisted }),
      });
      setMsg(`Queued ${jobs.length} verifications — they run one after another.`);
    } catch (e) {
      setMsg(String(e instanceof Error ? e.message : e));
    }
  }
  return (
    <Card title="Batch run" right={<span className="text-xs text-ink-2">{q ? `${q.running ?? 0} running · ${q.queued ?? 0} queued · ${q.done ?? 0} done` : ""}</span>}>
      <p className="mb-2 text-xs text-ink-2">
        Queue every package in the list above ({packages.length}, use the filter to narrow it) — e.g. to run overnight.
        {assisted ? " Assisted mode is on." : ""}
      </p>
      <div className="flex items-center gap-3">
        {(["A", "B"] as const).map((x) => (
          <label key={x} className="flex items-center gap-1.5 text-sm">
            <input
              type="checkbox"
              checked={paths.includes(x)}
              onChange={(e) => setPaths(e.target.checked ? [...paths, x].sort() as ("A" | "B")[] : paths.filter((p) => p !== x))}
            />
            <PathBadge path={x} />
          </label>
        ))}
        <button
          onClick={queue}
          disabled={!packages.length || !paths.length}
          className="ml-auto inline-flex items-center gap-1.5 rounded border border-[#2a78d6] px-3 py-1.5 text-sm font-semibold text-[#2a78d6] hover:bg-[#eff6fc] disabled:opacity-40"
        >
          <Layers size={14} /> Queue {packages.length * paths.length}
        </button>
      </div>
      {msg && <p className="mt-2 text-xs text-ink-2">{msg}</p>}
    </Card>
  );
}

function UploadCard({ onDone }: { onDone: (id: string) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("UPLOAD-001");
  const [files, setFiles] = useState<File[]>([]);
  const [state, setState] = useState<string>();

  async function submit() {
    const fd = new FormData();
    fd.append("name", name);
    files.forEach((f) => fd.append("files", f));
    setState("Uploading…");
    try {
      const r = await api<{ id: string; files: string[] }>("/api/packages", { method: "POST", body: fd });
      setState(`Saved ${r.files.length} PDF(s)`);
      setFiles([]);
      onDone(r.id);
    } catch (e) {
      setState(String(e instanceof Error ? e.message : e));
    }
  }

  return (
    <Card title="Upload a package">
      <div
        onClick={() => input.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          setFiles([...e.dataTransfer.files].filter((f) => f.name.toLowerCase().endsWith(".pdf")));
        }}
        className="flex cursor-pointer flex-col items-center gap-1 rounded border border-dashed border-[#c8c6c4] px-4 py-5 text-center text-sm text-ink-2 hover:border-[#2a78d6]"
      >
        <Upload size={20} />
        {files.length
          ? `${files.length} PDF(s): ${files.map((f) => f.name).join(", ")}`
          : "Drop the PO, delivery note, goods receipt and invoice PDFs here, or click. The MSA comes from the contract library."}
        <input ref={input} type="file" accept="application/pdf" multiple hidden onChange={(e) => setFiles([...(e.target.files ?? [])])} />
      </div>
      <div className="mt-3 flex gap-2">
        <input value={name} onChange={(e) => setName(e.target.value)} className="min-w-0 flex-1 rounded border border-line px-2 py-1.5 text-sm" aria-label="Package name" />
        <button
          onClick={submit}
          disabled={!files.length || !name}
          className="rounded border border-[#2a78d6] px-3 py-1.5 text-sm font-semibold text-[#2a78d6] hover:bg-[#eff6fc] disabled:opacity-40"
        >
          Save
        </button>
      </div>
      {state && <p className="mt-2 text-xs text-ink-2">{state}</p>}
    </Card>
  );
}
