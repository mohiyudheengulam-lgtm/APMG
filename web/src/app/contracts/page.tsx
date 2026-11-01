"use client";

import { useRef, useState } from "react";
import { FilePlus2, FileText, Pencil, Trash2, Upload, X } from "lucide-react";
import { Contract, api, useApi } from "@/lib/api";
import { num, when } from "@/lib/format";
import { Card, Empty, ErrorNote, Kpi, PageHeader, Spinner } from "@/components/ui";

export default function ContractsPage() {
  const { data: list, error, reload } = useApi<Contract[]>("/api/contracts");
  const msas = (list ?? []).filter((c) => c.kind === "msa");
  const guidelines = (list ?? []).filter((c) => c.kind === "guideline");

  return (
    <>
      <PageHeader
        title="Contract library"
        sub="Partner master agreements and the purchasing guideline are added once. Packages then only need PO, delivery note, goods receipt and invoice — the matching contract is linked by its number on the invoice or PO."
      />
      <ErrorNote error={error} />
      <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi accent label="Master agreements" value={num(msas.length)} sub="one per partner" />
        <Kpi label="Guidelines" value={num(guidelines.length)} sub="buyer-side rules" />
        <Kpi label="Linked packages" value={num(new Set((list ?? []).flatMap((c) => c.packages)).size)} sub="with a contract on file" />
        <Kpi label="Contract pages" value={num((list ?? []).reduce((s, c) => s + c.pages, 0))} sub="indexed once, reused" />
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-3">
          {!list ? (
            <Spinner label="Loading…" />
          ) : !list.length ? (
            <Empty>No contracts yet — add your first partner MSA on the right.</Empty>
          ) : (
            [...msas, ...guidelines].map((c) => <ContractCard key={c.id} c={c} onChange={reload} />)
          )}
        </div>
        <AddContract onDone={reload} />
      </div>
    </>
  );
}

function ContractCard({ c, onChange }: { c: Contract; onChange: () => void }) {
  const [editing, setEditing] = useState(false);
  const [terms, setTerms] = useState(c.match_terms.join(", "));
  const [err, setErr] = useState<string>();

  async function save() {
    try {
      await api(`/api/contracts/${c.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ match_terms: terms.split(",").map((t) => t.trim()).filter(Boolean) }),
      });
      setEditing(false);
      onChange();
    } catch (e) {
      setErr(String(e instanceof Error ? e.message : e));
    }
  }
  async function remove() {
    if (!confirm(`Remove ${c.filename} from the library? Linked packages will no longer find it.`)) return;
    await api(`/api/contracts/${c.id}`, { method: "DELETE" });
    onChange();
  }

  const supplier = c.kind === "msa" ? c.parties[1] ?? c.parties[0] : c.parties[0];
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${c.kind === "msa" ? "bg-[#eff6fc] text-[#1c5cab]" : "bg-[#f3f2f1] text-ink-2"}`}>
              {c.kind === "msa" ? "Master agreement" : "Guideline"}
            </span>
            <a href={`/api/contracts/${c.id}/file`} target="_blank" className="inline-flex items-center gap-1 text-[15px] font-semibold hover:underline">
              <FileText size={14} /> {c.filename}
            </a>
          </div>
          <div className="mt-1 text-[13px] text-ink-2">
            {c.kind === "msa" ? (
              <>
                {c.number && <b className="text-ink">{c.number}</b>} · partner <b className="text-ink">{supplier ?? "–"}</b>
                {c.parties[0] && c.parties[1] ? ` · buyer ${c.parties[0]}` : ""}
              </>
            ) : (
              <>for {supplier ?? "–"}</>
            )}{" "}
            · {c.pages} pages · added {when(c.added_at)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-2">Linked packages</div>
          <div className="num text-2xl font-semibold">{c.packages.length}</div>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-ink-2">Matched by:</span>
        {editing ? (
          <>
            <input value={terms} onChange={(e) => setTerms(e.target.value)} className="min-w-0 flex-1 rounded border border-line px-2 py-1 text-sm" />
            <button onClick={save} className="rounded bg-[#2a78d6] px-3 py-1 font-semibold text-white">Save</button>
            <button onClick={() => setEditing(false)} aria-label="Cancel" className="text-ink-2"><X size={14} /></button>
          </>
        ) : (
          <>
            {c.match_terms.length ? (
              c.match_terms.map((t) => <code key={t} className="rounded bg-[#f3f2f1] px-1.5 py-0.5">{t}</code>)
            ) : (
              <span className="text-[#a4262c]">nothing — this contract is never linked</span>
            )}
            <button onClick={() => setEditing(true)} className="inline-flex items-center gap-1 text-[#2a78d6] hover:underline"><Pencil size={11} /> edit</button>
          </>
        )}
        <span className="ml-auto flex items-center gap-3 text-ink-2">
          {Object.entries(c.build ?? {}).map(([p, b]) => (
            <span key={p} title="one-off preparation for this retrieval path">Path {p}: {num(b.build_seconds, 1)} s</span>
          ))}
          <button onClick={remove} className="inline-flex items-center gap-1 text-[#a4262c] hover:underline"><Trash2 size={12} /> remove</button>
        </span>
      </div>
      {err && <p className="mt-2 text-xs text-[#a4262c]">{err}</p>}
    </Card>
  );
}

function AddContract({ onDone }: { onDone: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [terms, setTerms] = useState("");
  const [state, setState] = useState<{ ok?: string; err?: string; busy?: boolean }>({});

  async function submit() {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("match_terms", terms);
    setState({ busy: true });
    try {
      const c = await api<Contract>("/api/contracts", { method: "POST", body: fd });
      setState({ ok: `Added ${c.filename}${c.number ? ` (${c.number})` : ""} — linked to ${c.packages.length} package(s).` });
      setFile(null);
      setTerms("");
      onDone();
    } catch (e) {
      setState({ err: String(e instanceof Error ? e.message : e) });
    }
  }

  return (
    <Card title="Add contract" className="lg:sticky lg:top-16 lg:self-start">
      <div
        onClick={() => input.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          setFile([...e.dataTransfer.files].find((f) => f.name.toLowerCase().endsWith(".pdf")) ?? null);
        }}
        className="flex cursor-pointer flex-col items-center gap-1 rounded border border-dashed border-[#c8c6c4] px-4 py-6 text-center text-sm text-ink-2 hover:border-[#2a78d6]"
      >
        {file ? <FilePlus2 size={22} className="text-[#2a78d6]" /> : <Upload size={22} />}
        {file ? file.name : "Drop a partner's master agreement (or the purchasing guideline) as PDF, or click"}
        <input ref={input} type="file" accept="application/pdf" hidden onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </div>
      <label className="mt-3 block text-xs text-ink-2">
        Match terms (optional, comma-separated)
        <input
          value={terms}
          onChange={(e) => setTerms(e.target.value)}
          placeholder="auto-detected: contract number / company name"
          className="mt-1 w-full rounded border border-line px-2 py-1.5 text-sm"
        />
      </label>
      <button
        onClick={submit}
        disabled={!file || state.busy}
        className="mt-3 w-full rounded bg-[#2a78d6] px-4 py-2 text-sm font-semibold text-white hover:bg-[#256abf] disabled:opacity-50"
      >
        {state.busy ? "Reading contract…" : "Add to library"}
      </button>
      <p className="mt-2 text-xs text-ink-2">
        The contract number and parties are read automatically. Invoices and POs quoting that number are linked to this contract.
        Search indexes are built once, the first time a linked package is verified.
      </p>
      {state.ok && <p className="mt-2 text-xs font-semibold text-[#107c10]">{state.ok}</p>}
      {state.err && <p className="mt-2 text-xs text-[#a4262c]">{state.err}</p>}
    </Card>
  );
}
