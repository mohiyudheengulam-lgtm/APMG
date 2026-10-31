"""Agent On Duty — local Streamlit app (Exposé §5.6), report-style layout.

    uv run streamlit run src/agent_on_duty/ui/app.py

Pages: Overview (KPIs + charts), Verify (upload & run), Evidence (verification trace),
Approvals (manager HITL gate), Benchmark (Path A vs Path B results).
Private model reasoning is not shown — only auditable actions and evidence.
"""

import json
import shutil
import zipfile
from decimal import Decimal
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from agent_on_duty import pipeline
from agent_on_duty.audit.store import RecommendationWriter, approve, list_verifications
from agent_on_duty.schemas import Decision

ROOT = Path(__file__).resolve().parents[3]  # noqa: E305
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
INDEX = DATA / "index"
RESULTS = ROOT / "results"
APP_DIR = RESULTS / "app"
DB = APP_DIR / "aod.sqlite"
WRITER = RecommendationWriter(DB, APP_DIR / "audit")

# chart tokens (dataviz reference palette, light)
SERIES = {"A": "#2a78d6", "B": "#eb6834"}
BAR = "#2a78d6"
INK, INK_2, MUTED, GRID, AXIS = "#252423", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
FLAG_LABEL = {
    "FLAGGED_PRICE_MISMATCH": "Price", "FLAGGED_QUANTITY_MISMATCH": "Quantity",
    "FLAGGED_LINE_TOTAL_MISMATCH": "Line total", "FLAGGED_SURCHARGE": "Surcharge",
    "FLAGGED_MISSING_DOCUMENT": "Missing document",
}

st.set_page_config(page_title="Agent On Duty", page_icon="🧾", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
#MainMenu, footer, header[data-testid="stHeader"] {visibility: hidden; height: 0;}
html, body, [class*="css"], .stApp {font-family: "Segoe UI", system-ui, -apple-system, sans-serif;}
.stApp {background: #f3f2f1;}
.block-container {padding-top: 4.2rem; padding-bottom: 2rem; max-width: 1500px;}
.aod-topbar {position: fixed; top: 0; left: 0; right: 0; height: 48px; z-index: 999990;
  background: #252423; color: #fff; display: flex; align-items: center; gap: 12px; padding: 0 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,.25);}
.aod-logo {width: 22px; height: 22px; border-radius: 3px; background: linear-gradient(135deg,#f2c811 0 50%,#e8a800 50%);}
.aod-title {font-weight: 600; font-size: 15px; letter-spacing: .2px;}
.aod-sep {color: #8a8886; font-size: 14px;}
.aod-crumb {color: #d2d0ce; font-size: 14px;}
.aod-badge {margin-left: auto; font-size: 12px; color: #d2d0ce; border: 1px solid #484644; padding: 3px 10px; border-radius: 12px;}
section[data-testid="stSidebar"] {background: #faf9f8; border-right: 1px solid #e1dfdd; top: 48px;}
section[data-testid="stSidebar"] .stRadio label p {font-size: 14px;}
[class*="st-key-card-"] {background: #fff; border: 1px solid #e1dfdd; border-radius: 4px; padding: 14px 16px 12px 16px;
  box-shadow: 0 1.6px 3.6px rgba(0,0,0,.08), 0 .3px .9px rgba(0,0,0,.06);}
section[data-testid="stSidebar"] [data-testid="stRadio"] label {padding: 7px 10px; border-radius: 4px; width: 100%;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background: #edebe9; font-weight: 600;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {display: none;}
.aod-kpi {padding: 2px 4px;}
.aod-kpi .lbl {font-size: 12px; color: #605e5c; text-transform: uppercase; letter-spacing: .4px; font-weight: 600;}
.aod-kpi .val {font-size: 30px; font-weight: 600; color: #252423; line-height: 1.25; margin-top: 2px;}
.aod-kpi .sub {font-size: 12px; color: #605e5c;}
.aod-kpi.accent {border-left: 4px solid #f2c811; padding-left: 10px;}
.aod-h {font-size: 14px; font-weight: 600; color: #252423; margin: 0 0 6px 0;}
.aod-page {font-size: 20px; font-weight: 600; color: #252423; margin: 0 0 2px 0;}
.aod-pagesub {font-size: 13px; color: #605e5c; margin-bottom: 14px;}
.aod-chip {display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 9px; border-radius: 10px; margin: 0 4px 4px 0;}
.chip-flag {background: #fde7e9; color: #a4262c;} .chip-ok {background: #dff6dd; color: #107c10;}
.chip-warn {background: #fff4ce; color: #797673;} .chip-pend {background: #e1dfdd; color: #323130;}
.aod-finding {border-left: 3px solid #d13438; background: #fdf6f6; padding: 8px 12px; margin: 6px 0; border-radius: 2px; font-size: 13px;}
.aod-finding .ev {color: #605e5c; font-size: 12px;}
div[data-testid="stMetric"] {background: transparent;}
</style>
"""


_cards = iter(range(10_000))


def card(parent=st):
    """White report tile (styled via its key)."""
    return parent.container(key=f"card-{next(_cards)}")


def topbar(page: str):
    bar = ('<div class="aod-topbar"><div class="aod-logo"></div><span class="aod-title">Agent On Duty</span>'
           f'<span class="aod-sep">/</span><span class="aod-crumb">{page}</span>'
           f'<span class="aod-badge">{SOURCE_LABEL} · Qwen3-1.7B · Ollama · local</span></div>')
    st.markdown(CSS + bar, unsafe_allow_html=True)


def page_title(title: str, sub: str):
    st.markdown(f'<div class="aod-page">{title}</div><div class="aod-pagesub">{sub}</div>', unsafe_allow_html=True)


def kpi(col, label: str, value: str, sub: str = "", accent: bool = False):
    with card(col):
        st.markdown(f'<div class="aod-kpi{" accent" if accent else ""}"><div class="lbl">{label}</div>'
                    f'<div class="val">{value}</div><div class="sub">{sub or "&nbsp;"}</div></div>', unsafe_allow_html=True)


def chips(rec: str | None) -> str:
    if rec is None:
        return '<span class="aod-chip chip-warn">⚠ No valid recommendation</span>'
    if rec == "NO_DISCREPANCY":
        return '<span class="aod-chip chip-ok">✓ No discrepancy</span>'
    return "".join(f'<span class="aod-chip chip-flag">⚑ {FLAG_LABEL.get(f, f)}</span>' for f in rec.split(","))


def _style(chart: alt.Chart, height: int = 240) -> alt.Chart:
    return (chart.properties(height=height, background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelColor=MUTED, titleColor=INK_2, gridColor=GRID, domainColor=AXIS, tickColor=AXIS,
                            labelFont="Segoe UI", titleFont="Segoe UI", labelFontSize=11, titleFontSize=11, titleFontWeight=400)
            .configure_legend(labelColor=INK_2, titleColor=INK_2, labelFont="Segoe UI", titleFont="Segoe UI", orient="top"))


def hbar(df: pd.DataFrame, cat: str, val: str, title: str, fmt: str = ",.0f", height: int = 220) -> alt.Chart:
    base = alt.Chart(df).encode(
        y=alt.Y(f"{cat}:N", sort="-x", title=None, axis=alt.Axis(grid=False, ticks=False, labelColor=INK_2)),
        x=alt.X(f"{val}:Q", title=title, axis=alt.Axis(grid=True, tickCount=4, format=fmt)),
        tooltip=[alt.Tooltip(f"{cat}:N"), alt.Tooltip(f"{val}:Q", format=fmt)],
    )
    bars = base.mark_bar(color=BAR, cornerRadiusEnd=4, size=18)
    labels = base.mark_text(align="left", dx=4, color=INK_2, fontSize=11).encode(text=alt.Text(f"{val}:Q", format=fmt))
    return _style(bars + labels, height)


def grouped(df: pd.DataFrame, cat: str, val: str, title: str, fmt: str = ".0f", height: int = 260) -> alt.Chart:
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=16).encode(
        x=alt.X(f"{cat}:N", title=None, axis=alt.Axis(labelAngle=0, ticks=False, labelColor=INK_2)),
        xOffset=alt.XOffset("Path:N"),
        y=alt.Y(f"{val}:Q", title=title, axis=alt.Axis(tickCount=5, format=fmt)),
        color=alt.Color("Path:N", scale=alt.Scale(domain=list(SERIES), range=list(SERIES.values())),
                        legend=alt.Legend(title=None, labelExpr="'Path ' + datum.label")),
        tooltip=["Path:N", f"{cat}:N", alt.Tooltip(f"{val}:Q", format=fmt)],
    )
    return _style(chart, height)


# ------------------------------------------------------------------ data

def _packages() -> dict[str, Path]:
    out = {}
    for base in (DATA / "packages", UPLOADS):
        if base.exists():
            out |= {p.name: p for p in sorted(base.iterdir()) if p.is_dir() and any(p.glob("*.pdf"))}
    return out


def _audit(row: dict) -> dict:
    try:
        return json.loads(Path(row["audit_path"]).read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _frame() -> pd.DataFrame:
    rows = list_verifications(DB)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    audits = [_audit(r) for r in rows]
    df["impact_eur"] = [float(sum((Decimal(str(f.get("amount") or 0)) for f in (a.get("findings") or [])), Decimal(0)))
                        for a in audits]
    df["seconds"] = [a.get("seconds_total") for a in audits]
    df["tokens"] = [a.get("prompt_tokens_total") for a in audits]
    df["flagged"] = df["recommendation"].notna() & df["recommendation"].ne("NO_DISCREPANCY")
    df["no_result"] = df["recommendation"].isna()
    return df


# ------------------------------------------------------------------ pages

def page_overview():
    topbar("Overview")
    page_title("Verification overview", "All invoice verifications recorded by this workstation.")
    df = _frame()
    if df.empty:
        st.info("No verifications yet — run one under **Verify**.")
        return
    pending = df[df["review_state"] == "PENDING_REVIEW"]
    c = st.columns(5)
    kpi(c[0], "Verifications", f"{len(df)}", f"{df['package_id'].nunique()} packages", accent=True)
    kpi(c[1], "Pending review", f"{len(pending)}", f"{int(pending['flagged'].sum())} flagged")
    kpi(c[2], "Flag rate", f"{df['flagged'].mean():.0%}", f"{int(df['no_result'].sum())} without valid result")
    kpi(c[3], "Discrepancy value", f"€{df['impact_eur'].sum():,.0f}", "sum of flagged amounts")
    kpi(c[4], "Median time", f"{df['seconds'].median():.0f}s", "per verification")

    left, right = st.columns([1, 1])
    flags = df["recommendation"].dropna().str.split(",").explode()
    flags = flags[flags != "NO_DISCREPANCY"].map(lambda f: FLAG_LABEL.get(f, f)).value_counts()
    with card(left):
        st.markdown('<div class="aod-h">Discrepancies by type</div>', unsafe_allow_html=True)
        if len(flags):
            st.altair_chart(hbar(flags.rename_axis("Type").reset_index(name="Count"), "Type", "Count", "Flags raised"),
                            width="stretch")
        else:
            st.caption("No flags raised yet.")
    with card(right):
        st.markdown('<div class="aod-h">Discrepancy value by package (€)</div>', unsafe_allow_html=True)
        by_pkg = df.groupby("package_id", as_index=False)["impact_eur"].max().nlargest(8, "impact_eur")
        by_pkg = by_pkg[by_pkg["impact_eur"] > 0]
        if len(by_pkg):
            st.altair_chart(hbar(by_pkg.rename(columns={"package_id": "Package", "impact_eur": "EUR"}), "Package", "EUR",
                                 "EUR", fmt=",.0f"), width="stretch")
        else:
            st.caption("No monetary discrepancies yet.")

    with card():
        st.markdown('<div class="aod-h">Awaiting manager review</div>', unsafe_allow_html=True)
        tbl = pending.sort_values(["flagged", "impact_eur"], ascending=False)[
            ["package_id", "path", "recommendation", "impact_eur", "seconds", "created_at"]].assign(
                recommendation=lambda d: d["recommendation"].fillna("⚠ no valid result")).rename(columns={
                "package_id": "Package", "path": "Path", "recommendation": "Recommendation",
                "impact_eur": "Impact (€)", "seconds": "Time (s)", "created_at": "Created"})
        st.dataframe(tbl, hide_index=True, width="stretch", column_config={
            "Impact (€)": st.column_config.ProgressColumn(format="€%.0f", min_value=0,
                                                          max_value=float(max(tbl["Impact (€)"].max() or 1, 1))),
            "Time (s)": st.column_config.NumberColumn(format="%.0f")})


def page_verify():
    topbar("Verify")
    page_title("Verify a package", "Upload a procurement package and let the agent prepare a recommendation.")
    left, right = st.columns([1, 2])
    with card(left):
        st.markdown('<div class="aod-h">Upload package</div>', unsafe_allow_html=True)
        name = st.text_input("Package name", value="UPLOAD-001")
        files = st.file_uploader("PO, goods receipt, invoice, MSA (PDF or .zip)", type=["pdf", "zip"],
                                 accept_multiple_files=True)
        if st.button("Save package", disabled=not files, width="stretch"):
            target = UPLOADS / name
            shutil.rmtree(target, ignore_errors=True)
            target.mkdir(parents=True)
            for f in files:
                if f.name.endswith(".zip"):
                    with zipfile.ZipFile(f) as z:
                        for member in z.namelist():
                            if member.lower().endswith(".pdf") and not member.startswith("__MACOSX"):
                                (target / Path(member).name).write_bytes(z.read(member))
                else:
                    (target / Path(f.name).name).write_bytes(f.getvalue())
            st.success(f"Saved {len(list(target.glob('*.pdf')))} PDF(s) as {name}")

    pkgs = _packages()
    with card(right):
        st.markdown('<div class="aod-h">Run verification</div>', unsafe_allow_html=True)
        if not pkgs:
            st.info("No packages yet. Generate the benchmark or upload one.")
            return
        c1, c2 = st.columns([3, 2])
        pkg = c1.selectbox("Package", list(pkgs))
        path = c2.radio("Retrieval path", ["A", "B"], horizontal=True, format_func=lambda p: {
            "A": "A · Vector RAG", "B": "B · OKF navigation"}[p])
        st.caption("📄 " + " · ".join(p.name for p in sorted(pkgs[pkg].glob("*.pdf"))))
        if st.button("▶  Run verification", type="primary", width="stretch"):
            with st.status(f"Verifying {pkg} via Path {path} …", expanded=True) as status:
                st.write("Extracting documents and building the retrieval index …")
                build = pipeline.prepare(pkgs[pkg], path, INDEX)
                st.write(f"Index ready ({build['build_seconds']:.1f}s). Agent running (≤10 steps) …")
                _, vid = pipeline.verify(pkgs[pkg], path, INDEX, WRITER, extra={"source": "app"})
                status.update(label=f"Saved as PENDING_REVIEW · {vid}", state="complete")
            st.session_state["selected_vid"] = vid

    vid = st.session_state.get("selected_vid")
    if vid and (APP_DIR / "audit" / f"{vid}.json").exists():
        audit = json.loads((APP_DIR / "audit" / f"{vid}.json").read_text())
        with card():
            st.markdown(f'<div class="aod-h">Recommendation</div>{chips(audit["recommendation"])}', unsafe_allow_html=True)
            st.caption("The agent only recommends — the decision is made under **Approvals**.")
            render_trace(audit)


def render_findings(audit: dict):
    for f in audit.get("findings") or []:
        ev = " · ".join(f"{e['document']} p.{e['page']}" for e in f["evidence"])
        amt = f" — <b>€{Decimal(str(f['amount'])):,.2f}</b>" if f.get("amount") else ""
        item = f" · item {f['item_no']}" if f.get("item_no") else ""
        st.markdown(f'<div class="aod-finding"><b>{FLAG_LABEL.get(f["flag"], f["flag"])}</b>{item}{amt}<br>'
                    f'{f.get("formula") or ""}<br><span class="ev">Evidence: {ev}</span></div>', unsafe_allow_html=True)


def render_trace(audit: dict):
    c = st.columns(4)
    c[0].metric("Status", audit["run_status"])
    c[1].metric("Time", f"{audit['seconds_total']:.0f}s")
    c[2].metric("Input tokens", f"{audit['prompt_tokens_total']:,}")
    c[3].metric("Steps / invalid calls", f"{len(audit['steps'])} / {audit['invalid_tool_calls']}")
    render_findings(audit)
    tabs = st.tabs(["Tool calls", "Calculations", "Cited clauses", "Submitted values"])
    with tabs[0]:
        for s in audit["steps"]:
            calls = s["tool_calls"]
            with st.expander(f"Step {s['step']} — " + (", ".join(c["name"] for c in calls) or "no tool call")
                             + f"   ·  {s['seconds']:.1f}s  ·  {s['prompt_tokens']:,} tokens"):
                for call in calls:
                    st.markdown(f"**{call['name']}**")
                    if call["arguments"]:
                        st.json(call["arguments"], expanded=False)
                    st.code(call["result"][:3000], language="markdown")
    with tabs[1]:
        if audit["calculations"]:
            st.dataframe(pd.DataFrame(audit["calculations"])[["flag", "item_no", "expected", "actual", "amount", "formula"]],
                         hide_index=True, width="stretch")
        else:
            st.caption("No differences computed.")
    with tabs[2]:
        if audit["cited_clauses"]:
            st.dataframe(pd.DataFrame(audit["cited_clauses"]), hide_index=True, width="stretch")
        else:
            st.caption("No clause cited.")
    with tabs[3]:
        st.json(audit["submitted_values"], expanded=False)


def page_evidence():
    topbar("Evidence")
    page_title("Verification evidence", "Every tool call, retrieved passage, calculation and citation of a verification.")
    rows = list_verifications(DB)
    if not rows:
        st.info("No verifications yet.")
        return
    labels = {r["id"]: f"{r['package_id']} · Path {r['path']} · {r['created_at']} · {r['review_state']}" for r in rows}
    ids = list(labels)
    default = ids.index(st.session_state["selected_vid"]) if st.session_state.get("selected_vid") in ids else 0
    vid = st.selectbox("Verification", ids, index=default, format_func=labels.get)
    audit = _audit(next(r for r in rows if r["id"] == vid))
    with card():
        st.markdown(chips(audit.get("recommendation")), unsafe_allow_html=True)
        render_trace(audit)


def page_approvals():
    topbar("Approvals")
    page_title("Manager approvals", "Human-in-the-loop gate: only a manager decision becomes final.")
    df = _frame()
    if df.empty:
        st.info("Nothing to review yet.")
        return
    pending = df[df["review_state"] == "PENDING_REVIEW"].sort_values(["flagged", "impact_eur"], ascending=False)
    reviewed = df[df["review_state"] == "REVIEWED"]
    c = st.columns(4)
    kpi(c[0], "Pending", f"{len(pending)}", accent=True)
    kpi(c[1], "Flagged & pending", f"{int(pending['flagged'].sum())}")
    kpi(c[2], "Reviewed", f"{len(reviewed)}")
    kpi(c[3], "Overrides", f"{int((reviewed['decision'] == 'OVERRIDDEN').sum())}")

    for _, r in pending.iterrows():
        audit = _audit(r)
        with card():
            head, val = st.columns([4, 1])
            head.markdown(f'<div class="aod-h">{r["package_id"]} · Path {r["path"]}</div>{chips(r["recommendation"])}'
                          f'<div class="aod-pagesub">{r["created_at"]}</div>', unsafe_allow_html=True)
            val.markdown(f'<div class="aod-kpi"><div class="lbl">Impact</div><div class="val">€{r["impact_eur"]:,.0f}</div></div>',
                         unsafe_allow_html=True)
            render_findings(audit)
            with st.form(f"decide-{r['id']}", border=False):
                f1, f2 = st.columns([1, 2])
                reviewer = f1.text_input("Reviewer", key=f"rv-{r['id']}")
                choice = f2.radio("Decision", ["Confirm recommendation", "Override", "Reject invoice"],
                                  horizontal=True, key=f"ch-{r['id']}")
                reason = st.text_input("Override reason (required for override)", key=f"rs-{r['id']}")
                if st.form_submit_button("Record decision", type="primary"):
                    decision = {"Confirm recommendation": Decision.APPROVED, "Override": Decision.OVERRIDDEN,
                                "Reject invoice": Decision.REJECTED}[choice]
                    if not reviewer.strip():
                        st.error("Reviewer name is required.")
                    else:
                        try:
                            approve(DB, r["id"], decision, reviewer.strip(), reason.strip() or None)
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

    if len(reviewed):
        with card():
            st.markdown('<div class="aod-h">Decision log</div>', unsafe_allow_html=True)
            st.dataframe(reviewed[["package_id", "path", "recommendation", "decision", "reviewer", "decided_at",
                                   "override_reason"]], hide_index=True, width="stretch")


def page_benchmark():
    topbar("Benchmark")
    page_title("Benchmark · Path A vs Path B", "Controlled comparison on the generated corpus (Exposé §6). Descriptive only.")
    tags = sorted(p.parent.name for p in RESULTS.glob("*/summary.json"))
    if not tags:
        st.info("No evaluated benchmark yet. Run `scripts/run_benchmark.py` then `scripts/evaluate.py`.")
        return
    tag = st.selectbox("Result set", tags, index=len(tags) - 1)
    s = json.loads((RESULTS / tag / "summary.json").read_text())
    paths = [p for p in ("A", "B") if p in s]

    def pair(metric: str, fmt) -> str:
        return " · ".join(f"{p}: {fmt(s[p][metric])}" for p in paths)

    c = st.columns(5)
    kpi(c[0], "Field accuracy (EM)", pair("field_em", lambda v: f"{v:.0f}%"), "extracted values", accent=True)
    kpi(c[1], "Flag F1 (micro)", " · ".join(f"{p}: {s[p]['flag_micro'][2]:.2f}" for p in paths), "all flag types")
    kpi(c[2], "Median latency", pair("latency_median_s", lambda v: f"{v:.0f}s"), "per verification")
    kpi(c[3], "Input tokens", pair("prompt_tokens_mean", lambda v: f"{v / 1000:.1f}k"), "mean per verification")
    kpi(c[4], "Unsigned decisions", f"{s['_governance']['decisions_without_signoff']}", "expected 0")

    acc = pd.DataFrame([{"Path": p, "Metric": m, "Value": s[p][k]} for p in paths for m, k in
                        [("Field EM", "field_em"), ("Calculation EM", "calc_em"), ("Clause citation", "citation_acc"),
                         ("Recommendation", "recommendation_acc"), ("Valid output", "valid_share"),
                         ("Evidence complete", "evidence_complete_share")]])
    flags = pd.DataFrame([{"Path": p, "Flag": FLAG_LABEL[f], "F1": v[2]} for p in paths for f, v in s[p]["flags"].items()])
    cases = pd.DataFrame([{"Path": p, "Case": k.replace("_", " "), "Correct %": v} for p in paths
                          for k, v in s[p]["by_case"].items()])
    left, right = st.columns(2)
    with card(left):
        st.markdown('<div class="aod-h">Accuracy & reliability (%)</div>', unsafe_allow_html=True)
        st.altair_chart(grouped(acc, "Metric", "Value", "%"), width="stretch")
    with card(right):
        st.markdown('<div class="aod-h">Flag detection F1 by type</div>', unsafe_allow_html=True)
        st.altair_chart(grouped(flags, "Flag", "F1", "F1", fmt=".1f"), width="stretch")
    left, right = st.columns(2)
    with card(left):
        st.markdown('<div class="aod-h">Correct recommendation by case type (%)</div>', unsafe_allow_html=True)
        st.altair_chart(grouped(cases, "Case", "Correct %", "%"), width="stretch")
    with card(right):
        st.markdown('<div class="aod-h">Retrieval-path assignment (SQ3)</div>', unsafe_allow_html=True)
        for group, r in (s.get("_routing") or {}).items():
            st.markdown(f"**{group}** → Path **{r['path']}**  \n<span style='color:#605e5c;font-size:13px'>{r['reason']}</span>",
                        unsafe_allow_html=True)
        if not s.get("_routing"):
            st.caption("Needs results for both paths.")
        st.markdown('<div class="aod-h" style="margin-top:12px">Preparation</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"Path": p, "Build s": round(s[p]["prep_build_s_total"], 1),
                                    "Storage KB": round(s[p]["prep_storage_bytes"] / 1024),
                                    "Invalid calls %": round(s[p]["invalid_tool_call_rate"], 1),
                                    "Step limit %": round(s[p]["step_limit_share"], 1)} for p in paths]),
                     hide_index=True, width="stretch")
    runs_csv = RESULTS / tag / "runs.csv"
    if runs_csv.exists():
        with card():
            st.markdown('<div class="aod-h">All runs</div>', unsafe_allow_html=True)
            st.dataframe(pd.read_csv(runs_csv), hide_index=True, width="stretch")


PAGES = {"Overview": page_overview, "Verify": page_verify, "Evidence": page_evidence,
         "Approvals": page_approvals, "Benchmark": page_benchmark}
with st.sidebar:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    choice = st.radio("Navigation", list(PAGES), label_visibility="collapsed")
    sources = {"This workstation": APP_DIR} | {f"Benchmark · {d.name}": d for d in sorted(RESULTS.iterdir())
                                               if d.name != "app" and (d / "aod.sqlite").exists()} if RESULTS.exists() \
        else {"This workstation": APP_DIR}
    SOURCE_LABEL = st.selectbox("Data source", list(sources), help="Workstation runs or a benchmark result set")
    DB = sources[SOURCE_LABEL] / "aod.sqlite"
    st.markdown("<div style='margin-top:24px;font-size:12px;color:#605e5c'>APMG · Agent On Duty<br>"
                "Fully local · HITL approval gate</div>", unsafe_allow_html=True)
PAGES[choice]()
