"""Evaluation (Exposé §6.3–6.5): audit records + ground truth → results/<tag>/summary.md and CSVs.

    uv run python scripts/evaluate.py --tag full
"""

import argparse
import csv
import json
import statistics
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from agent_on_duty.audit.store import decisions_without_signoff

FLAGS = ["FLAGGED_PRICE_MISMATCH", "FLAGGED_QUANTITY_MISMATCH", "FLAGGED_LINE_TOTAL_MISMATCH",
         "FLAGGED_SURCHARGE", "FLAGGED_MISSING_DOCUMENT"]
ROUTING_MARGIN = 5.0  # percentage points (§6.4)


def dec(v) -> Decimal | None:
    try:
        return Decimal(str(v)) if v is not None else None
    except InvalidOperation:
        return None


# ------------------------------------------------------------------ per-run scoring

def score_fields(run: dict, gt: dict) -> tuple[int, int]:
    """EM over every ground-truth line field (quantity, unit_price, line_total) and invoice surcharge amount."""
    correct = total = 0
    for doc_type, expected in gt["fields"].items():
        submitted = {ln["item_no"]: ln for ln in (run["submitted_values"].get(doc_type) or {}).get("lines", [])}
        for line in expected["lines"]:
            got = submitted.get(line["item_no"], {})
            for key in ("quantity", "unit_price", "line_total"):
                if key in line:
                    total += 1
                    correct += dec(got.get(key)) == dec(line[key])
        if doc_type == "invoice":
            got_s = {s["label"].lower(): dec(s["amount"]) for s in
                     (run["submitted_values"].get("invoice") or {}).get("surcharges", [])}
            for s in expected["surcharges"]:
                total += 1
                correct += got_s.get(s["label"].lower()) == dec(s["amount"])
    return correct, total


def score_calculations(run: dict, gt: dict) -> tuple[int, int]:
    """EM of each expected variance amount (quantity, price, line total) against the tool calculations."""
    calcs = run.get("findings") or []
    correct = total = 0
    for f in gt["expected_findings"]:
        if f.get("error_type") in ("quantity", "price", "line_total"):
            total += 1
            correct += any(c["flag"] == f["flag"] and c.get("item_no") == f["item_no"] and dec(c.get("amount")) == dec(f["amount"])
                           for c in calcs)
    return correct, total


def score_citation(run: dict, gt: dict) -> tuple[int, int]:
    """Clause citation is correct only if document and page match (§6.3). Scored where a surcharge is present."""
    if not gt["surcharge_relevant"]:
        return 0, 0
    want = gt["msa_clauses"]["surcharges"]
    cites = run.get("cited_clauses") or []
    ok = bool(cites) and all(c["document"] == want["document"] and c["page"] == want["page"] for c in cites)
    return int(ok), 1


def predicted_flags(run: dict) -> set[str]:
    return set(run["recommendation"].split(",")) - {"NO_DISCREPANCY"} if run["recommendation"] else set()


def evidence_complete(run: dict, gt: dict) -> bool:
    """Every finding carries evidence, and every surcharge finding cites the correct MSA document and page."""
    want = gt["msa_clauses"]["surcharges"]
    for f in run.get("findings") or []:
        if not f.get("evidence"):
            return False
        if f["flag"] == "FLAGGED_SURCHARGE" and not any(
                e["document"] == want["document"] and e["page"] == want["page"] for e in f["evidence"]):
            return False
    return run["recommendation"] is not None


def error_cause(run: dict, gt: dict) -> str | None:
    """First-pass cause attribution (§6.5 step 5); flagged runs are reviewed manually afterwards."""
    if predicted_flags(run) == set(gt["expected_flags"]) and run["recommendation"] is not None:
        return None
    if run["run_status"] != "finished":
        return "invalid output format" if run["invalid_tool_calls"] else "step limit / no answer"
    expected_docs = set(gt["fields"])
    if not expected_docs <= set(run["submitted_values"]):
        return "retrieval miss"
    fc, ft = score_fields(run, gt)
    if fc < ft:
        return "retrieval miss" if run["invalid_tool_calls"] == 0 else "wrong tool use"
    cc, ct = score_citation(run, gt)
    if ct and not cc:
        return "wrong clause"
    calc_c, calc_t = score_calculations(run, gt)
    if calc_c < calc_t:
        return "incorrect calculation"
    return "wrong tool use"


# ------------------------------------------------------------------ aggregation

def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def pct(c, t):
    return 100.0 * c / t if t else float("nan")


def evaluate(tag: str, data: Path, index: Path) -> dict:
    out = Path("results") / tag
    runs = [json.loads(f.read_text()) for f in sorted((out / "audit").glob("*.json"))]
    runs = [r for r in runs if r.get("mode", "research") == "research"]  # assisted runs are never research data
    gts = {p.name: json.loads((p / "ground_truth.json").read_text()) for p in data.iterdir() if p.is_dir()}
    by_path = defaultdict(list)
    for r in runs:
        by_path[r["retrieval_path"]].append(r)

    per_run_rows, summary = [], {}
    for path, rs in sorted(by_path.items()):
        agg = defaultdict(int)
        flag_counts = {f: [0, 0, 0] for f in FLAGS}
        by_case = defaultdict(lambda: [0, 0])
        causes = defaultdict(int)
        latencies, tokens, tool_calls = [], [], 0
        for r in rs:
            gt = gts[r["package_id"]]
            fc, ft = score_fields(r, gt)
            cc, ct = score_calculations(r, gt)
            ci, cit = score_citation(r, gt)
            pred, exp = predicted_flags(r), set(gt["expected_flags"])
            for f in FLAGS:
                flag_counts[f][0] += f in pred and f in exp
                flag_counts[f][1] += f in pred and f not in exp
                flag_counts[f][2] += f not in pred and f in exp
            correct_rec = r["recommendation"] is not None and pred == exp
            by_case[gt["case_type"]][0] += correct_rec
            by_case[gt["case_type"]][1] += 1
            cause = error_cause(r, gt)
            if cause:
                causes[cause] += 1
            agg["field_c"] += fc; agg["field_t"] += ft
            agg["calc_c"] += cc; agg["calc_t"] += ct
            agg["cite_c"] += ci; agg["cite_t"] += cit
            agg["rec_c"] += correct_rec
            agg["valid"] += r["recommendation"] is not None
            agg["step_limit"] += r["run_status"] == "step_limit"
            agg["evidence"] += evidence_complete(r, gt)
            agg["invalid_calls"] += r["invalid_tool_calls"]
            n_calls = sum(len(s["tool_calls"]) for s in r["steps"])
            tool_calls += n_calls
            latencies.append(r["seconds_total"])
            tokens.append(r["prompt_tokens_total"])
            per_run_rows.append({
                "package_id": r["package_id"], "path": path, "run": r.get("run"), "case_type": gt["case_type"],
                "status": r["run_status"], "expected": gt["expected_recommendation"], "predicted": r["recommendation"],
                "correct": correct_rec, "field_em": f"{fc}/{ft}", "calc_em": f"{cc}/{ct}", "citation": f"{ci}/{cit}",
                "seconds": r["seconds_total"], "prompt_tokens": r["prompt_tokens_total"], "steps": len(r["steps"]),
                "tool_calls": n_calls, "invalid_tool_calls": r["invalid_tool_calls"], "cause": cause or "",
            })
        n = len(rs)
        run_pkgs = {r["package_id"] for r in rs}
        builds = [json.loads(b.read_text()) for b in (index / path).glob("*/build.json") if b.parent.name in run_pkgs]
        micro = [sum(v[i] for v in flag_counts.values()) for i in range(3)]
        summary[path] = {
            "runs": n,
            "field_em": pct(agg["field_c"], agg["field_t"]),
            "calc_em": pct(agg["calc_c"], agg["calc_t"]),
            "citation_acc": pct(agg["cite_c"], agg["cite_t"]),
            "recommendation_acc": pct(agg["rec_c"], n),
            "flags": {f: prf(*v) for f, v in flag_counts.items()},
            "flag_micro": prf(*micro),
            "surcharge_f1": prf(*flag_counts["FLAGGED_SURCHARGE"])[2] * 100,
            "latency_median_s": statistics.median(latencies) if latencies else float("nan"),
            "prompt_tokens_mean": statistics.mean(tokens) if tokens else float("nan"),
            "tokens_per_correct_field": (sum(tokens) / agg["field_c"]) if agg["field_c"] else float("nan"),
            "valid_share": pct(agg["valid"], n),
            "invalid_tool_call_rate": pct(agg["invalid_calls"], tool_calls),
            "step_limit_share": pct(agg["step_limit"], n),
            "evidence_complete_share": pct(agg["evidence"], n),
            "prep_build_s_total": sum(b["build_seconds"] for b in builds),
            "prep_extract_s_total": sum(b["extract_seconds"] for b in builds),
            "prep_storage_bytes": sum(b["storage_bytes"] for b in builds),
            "by_case": {k: pct(*v) for k, v in sorted(by_case.items())},
            "causes": dict(causes),
        }

    summary["_governance"] = {"decisions_without_signoff": decisions_without_signoff(out / "aod.sqlite")}
    summary["_routing"] = routing(summary)

    with open(out / "runs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_run_rows[0]))
        w.writeheader()
        w.writerows(per_run_rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    (out / "summary.md").write_text(render(tag, summary))
    return summary


def routing(summary: dict) -> dict:
    """§6.4: per source type, prefer the path ≥5 pp more accurate; otherwise the cheaper one (tokens, then latency)."""
    if not {"A", "B"} <= summary.keys():
        return {}
    a, b = summary["A"], summary["B"]
    groups = {"structured records (PO/GR/invoice)": "field_em", "MSA clauses": "citation_acc"}
    out = {}
    for group, metric in groups.items():
        diff = a[metric] - b[metric]
        if abs(diff) >= ROUTING_MARGIN:
            out[group] = {"path": "A" if diff > 0 else "B", "reason": f"{metric} differs by {abs(diff):.1f} pp"}
        else:
            cheaper = min(("A", "B"), key=lambda p: (summary[p]["prompt_tokens_mean"], summary[p]["latency_median_s"]))
            out[group] = {"path": cheaper, "reason": f"{metric} within {ROUTING_MARGIN} pp ({abs(diff):.1f}); lower token use/latency"}
    return out


def render(tag: str, s: dict) -> str:
    paths = [p for p in ("A", "B") if p in s]
    row = lambda label, fn: f"| {label} | " + " | ".join(fn(s[p]) for p in paths) + " |"
    f1 = lambda v: f"{v:.1f}"
    lines = [f"# Agent On Duty — results `{tag}`", "",
             "| Metric | " + " | ".join(f"Path {p}" for p in paths) + " |", "|---|" + "---|" * len(paths),
             row("Runs", lambda x: str(x["runs"])),
             "| **1. Accuracy** |" + " |" * len(paths),
             row("Field EM %", lambda x: f1(x["field_em"])),
             row("Calculation EM %", lambda x: f1(x["calc_em"])),
             row("Clause citation correct %", lambda x: f1(x["citation_acc"])),
             row("Recommendation exactly correct %", lambda x: f1(x["recommendation_acc"])),
             row("Flag micro P / R / F1", lambda x: " / ".join(f"{v:.2f}" for v in x["flag_micro"])),
             *[row(f"{fl.removeprefix('FLAGGED_')} F1", lambda x, fl=fl: f"{x['flags'][fl][2]:.2f}") for fl in FLAGS],
             "| **2. Latency** |" + " |" * len(paths),
             row("Median seconds / verification", lambda x: f1(x["latency_median_s"])),
             "| **3. Tokens** |" + " |" * len(paths),
             row("Mean input tokens / verification", lambda x: f"{x['prompt_tokens_mean']:.0f}"),
             row("Input tokens / correct field", lambda x: f"{x['tokens_per_correct_field']:.0f}"),
             "| **4. Preparation** |" + " |" * len(paths),
             row("Build seconds (all packages, incl. extraction)", lambda x: f"{x['prep_build_s_total']:.1f}"),
             row("Storage KB", lambda x: f"{x['prep_storage_bytes'] / 1024:.0f}"),
             "| **5. Reliability** |" + " |" * len(paths),
             row("Valid recommendation %", lambda x: f1(x["valid_share"])),
             row("Invalid tool-call rate %", lambda x: f1(x["invalid_tool_call_rate"])),
             row("Step limit reached %", lambda x: f1(x["step_limit_share"])),
             row("Evidence complete %", lambda x: f1(x["evidence_complete_share"])),
             "", f"Decisions recorded without manager sign-off: **{s['_governance']['decisions_without_signoff']}** (expected 0)",
             "", "Engineering hours: take from the sprint log.", "",
             "## Correct recommendation by case type (%)", "",
             "| Case | " + " | ".join(f"Path {p}" for p in paths) + " |", "|---|" + "---|" * len(paths)]
    for case in sorted({c for p in paths for c in s[p]["by_case"]}):
        lines.append(f"| {case} | " + " | ".join(f1(s[p]["by_case"].get(case, float('nan'))) for p in paths) + " |")
    lines += ["", "## Error causes (first pass)", ""]
    for p in paths:
        lines.append(f"- Path {p}: " + (", ".join(f"{k}: {v}" for k, v in sorted(s[p]["causes"].items())) or "none"))
    if s["_routing"]:
        lines += ["", "## Retrieval-path assignment (SQ3, §6.4)", ""]
        lines += [f"- **{g}** → Path {r['path']} ({r['reason']})" for g, r in s["_routing"].items()]
    lines += ["", "_Small corpus — descriptive only, no significance claims (§6.5)._"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="full")
    ap.add_argument("--data", type=Path, default=Path("data/packages"))
    ap.add_argument("--index", type=Path, default=Path("data/index"))
    args = ap.parse_args()
    evaluate(args.tag, args.data, args.index)
    print((Path("results") / args.tag / "summary.md").read_text())
