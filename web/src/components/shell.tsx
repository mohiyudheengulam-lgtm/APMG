"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { BarChart3, CheckSquare, ChevronsLeft, ChevronsRight, Cpu, FileSignature, FlaskConical, PlayCircle, ScanSearch, WifiOff } from "lucide-react";
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
    <div className="flex min-h-screen">
      <aside className={`shrink-0 bg-tile transition-[width] ${open ? "w-60" : "w-[76px]"}`}>
        <nav className="sticky top-0 flex h-screen flex-col px-3 py-5">
          <Link href="/" className="mb-8 flex items-center gap-2.5 px-2.5">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary text-[15px] font-black text-on-primary" aria-hidden>
              A
            </span>
            {open && <span className="text-[17px] font-bold tracking-tight">Agent On Duty</span>}
          </Link>
          <ul className="flex flex-col gap-1">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = current?.href === href;
              return (
                <li key={href}>
                  <Link
                    href={href}
                    title={label}
                    className={`flex items-center gap-3 rounded-full px-3.5 py-2.5 text-[15px] transition-colors ${
                      active ? "bg-primary-soft font-semibold text-primary-deep" : "text-ink-2 hover:bg-surface hover:text-ink"
                    }`}
                  >
                    <Icon size={20} strokeWidth={active ? 2.3 : 1.9} />
                    {open && <span>{label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
          <button
            onClick={() => setOpen(!open)}
            className="mt-auto flex items-center gap-3 rounded-full px-3.5 py-2.5 text-sm text-ink-2 hover:bg-surface"
            aria-label={open ? "Collapse navigation" : "Expand navigation"}
          >
            {open ? <ChevronsLeft size={18} /> : <ChevronsRight size={18} />}
            {open && "Collapse"}
          </button>
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 bg-canvas/85 px-8 backdrop-blur">
          <span className="text-sm font-medium text-ink-2">{current?.label ?? ""}</span>
          <div className="ml-auto flex items-center gap-2">
            {error ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-bad-soft px-3 py-1.5 text-xs font-semibold text-bad">
                <WifiOff size={13} /> API offline — start uvicorn
              </span>
            ) : null}
            <label className="flex items-center gap-2 rounded-full bg-tile py-1 pr-1 pl-3.5 text-xs font-medium text-ink-2 shadow-[0_0_0_1px_rgba(14,15,12,0.06)]">
              Data source
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="rounded-full bg-surface px-3 py-1.5 text-xs font-semibold text-ink outline-none focus:ring-2 focus:ring-primary"
              >
                {(sources ?? [{ id: "app", label: "This workstation" }]).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
            <span className="hidden items-center gap-1.5 rounded-full bg-tile px-3.5 py-2 text-xs font-medium text-ink-2 shadow-[0_0_0_1px_rgba(14,15,12,0.06)] md:inline-flex">
              <Cpu size={13} /> Qwen3-1.7B · local
            </span>
          </div>
        </header>
        <main className="min-w-0 flex-1 px-8 pt-2 pb-10">
          <div className="mx-auto max-w-[1400px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
