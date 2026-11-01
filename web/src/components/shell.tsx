"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { BarChart3, CheckSquare, ChevronsLeft, ChevronsRight, FileSignature, FlaskConical, PlayCircle, ScanSearch } from "lucide-react";
import { Source, useApi } from "@/lib/api";
import { useSource } from "./source";

const NAV = [
  { href: "/", label: "Overview", icon: BarChart3 },
  { href: "/verify", label: "Verify", icon: PlayCircle },
  { href: "/verifications", label: "Evidence", icon: ScanSearch },
  { href: "/approvals", label: "Approvals", icon: CheckSquare },
  { href: "/contracts", label: "Contracts", icon: FileSignature },
  { href: "/benchmark", label: "Benchmark", icon: FlaskConical },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [open, setOpen] = useState(true);
  const { source, setSource } = useSource();
  const { data: sources, error } = useApi<Source[]>("/api/sources", 15000);
  // a remembered data source can disappear (archived results): fall back to this workstation
  useEffect(() => {
    if (sources && !sources.some((s) => s.id === source)) setSource("app");
  }, [sources, source, setSource]);
  const current = NAV.find((n) => (n.href === "/" ? path === "/" : path.startsWith(n.href)));

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 flex h-12 items-center gap-3 bg-bar px-4 text-white shadow">
        <div className="h-[22px] w-[22px] rounded-[3px] bg-[linear-gradient(135deg,#f2c811_0_50%,#e8a800_50%)]" aria-hidden />
        <span className="text-[15px] font-semibold tracking-wide">Agent On Duty</span>
        <span className="text-[#8a8886]">/</span>
        <span className="text-sm text-[#d2d0ce]">{current?.label ?? ""}</span>
        <div className="ml-auto flex items-center gap-3">
          {error ? (
            <span className="rounded-full bg-[#a4262c] px-3 py-0.5 text-xs">API offline — start uvicorn</span>
          ) : null}
          <label className="flex items-center gap-2 text-xs text-[#d2d0ce]">
            Data source
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="rounded border border-[#484644] bg-[#323130] px-2 py-1 text-xs text-white outline-none focus:border-accent"
            >
              {(sources ?? [{ id: "app", label: "This workstation" }]).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          <span className="hidden rounded-full border border-[#484644] px-3 py-0.5 text-xs text-[#d2d0ce] md:inline">
            Qwen3-1.7B · Ollama · local
          </span>
        </div>
      </header>

      <div className="flex flex-1">
        <aside className={`shrink-0 border-r border-line bg-nav transition-[width] ${open ? "w-52" : "w-14"}`}>
        <nav className="sticky top-12 flex h-[calc(100vh-3rem)] flex-col">
          <ul className="mt-3 flex flex-col gap-0.5 px-2">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = current?.href === href;
              return (
                <li key={href}>
                  <Link
                    href={href}
                    title={label}
                    className={`flex items-center gap-3 rounded px-2.5 py-2 text-sm ${
                      active ? "bg-[#edebe9] font-semibold text-ink" : "text-ink-2 hover:bg-[#f3f2f1]"
                    }`}
                  >
                    <Icon size={18} strokeWidth={active ? 2.2 : 1.8} className={active ? "text-ink" : "text-ink-2"} />
                    {open && <span>{label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
          <button
            onClick={() => setOpen(!open)}
            className="mx-2 mt-auto mb-3 flex items-center gap-2 rounded px-2.5 py-2 text-xs text-ink-2 hover:bg-[#f3f2f1]"
            aria-label={open ? "Collapse navigation" : "Expand navigation"}
          >
            {open ? <ChevronsLeft size={16} /> : <ChevronsRight size={16} />}
            {open && "Collapse"}
          </button>
        </nav>
        </aside>
        <main className="min-w-0 flex-1 px-6 py-5">
          <div className="mx-auto max-w-[1500px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
