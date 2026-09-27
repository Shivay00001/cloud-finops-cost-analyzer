"""Presentable report renderers for FinOps analysis results.

Formats: text (CLI), markdown (file/PR-friendly), html (client-presentable,
fully self-contained: inline CSS, no external fonts or assets).
"""

from __future__ import annotations

import html as _html
from datetime import date


def _money(v: float) -> str:
    return f"${v:,.2f}"


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%"


# ---------------- text (CLI) ----------------

def render_text(summary: dict, client: str) -> str:
    lines = [
        "--- FinOps Cost Report ---",
        f"Client: {client}",
        f"Period: {summary['date_from']} to {summary['date_to']} "
        f"({summary['days_covered']} days, {summary['row_count']} rows)",
        f"Total Spend: {_money(summary['total_spend'])}",
        "",
        "--- Top Spenders by Service ---",
    ]
    for s in summary["top_services"]:
        lines.append(f"  {s['service']:<28} {_money(s['cost']):>12}  ({_pct(s['share'])})")
    if summary["top_regions"]:
        lines.append("")
        lines.append("--- Top Spenders by Region ---")
        for r in summary["top_regions"]:
            lines.append(f"  {r['region']:<28} {_money(r['cost']):>12}")
    lines.append("")
    lines.append("--- Anomalies Detected ---")
    if not summary["anomalies"]:
        lines.append("No anomalies detected.")
    else:
        for a in summary["anomalies"]:
            lines.append(
                f"  {a['date']}  {_money(a['cost']):>12}  "
                f"(+{_money(a['deviation'])} vs daily avg)"
            )
    lines.append("")
    lines.append("--- Forecast (Next 30 Days) ---")
    lines.append(f"Projected Spend: {_money(summary['forecast_30d'])}")
    return "\n".join(lines) + "\n"


# ---------------- markdown ----------------

def render_markdown(summary: dict, client: str) -> str:
    md = [
        f"# FinOps Cost Report — {client}",
        "",
        f"_Generated {date.today().isoformat()} · Period {summary['date_from']} → "
        f"{summary['date_to']} · {summary['days_covered']} days · "
        f"{summary['row_count']} billing rows_",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total spend | **{_money(summary['total_spend'])}** |",
        f"| Daily average | {_money(summary['daily_avg'])} |",
        f"| 30-day forecast | {_money(summary['forecast_30d'])} |",
        f"| Anomalies (>{summary['anomaly_threshold_std']}σ) | {len(summary['anomalies'])} |",
        "",
        "## Top services by spend",
        "",
        "| Service | Spend | Share |",
        "|---|---|---|",
    ]
    for s in summary["top_services"]:
        md.append(f"| {s['service']} | {_money(s['cost'])} | {_pct(s['share'])} |")
    if summary["top_regions"]:
        md += ["", "## Top regions by spend", "", "| Region | Spend |", "|---|---|"]
        for r in summary["top_regions"]:
            md.append(f"| {r['region']} | {_money(r['cost'])} |")
    md += ["", "## Anomalies", ""]
    if summary["anomalies"]:
        md += ["| Date | Spend | Above daily avg |", "|---|---|---|"]
        for a in summary["anomalies"]:
            md.append(f"| {a['date']} | {_money(a['cost'])} | +{_money(a['deviation'])} |")
    else:
        md.append("No anomalies detected in this period.")
    md += [
        "",
        "## 30-day forecast",
        "",
        f"Projected spend: **{_money(summary['forecast_30d'])}** "
        f"(linear projection: daily average × 30).",
        "",
        "_Method: daily spend grouped from the billing CSV; anomalies flagged "
        "where daily spend exceeds mean + N standard deviations; forecast is a "
        "straight-line daily-average projection._",
    ]
    return "\n".join(md) + "\n"


# ---------------- html (client-presentable) ----------------

_CSS = """
:root{--bg:#0f172a;--card:#1e293b;--accent:#38bdf8;--green:#34d399;--red:#f87171;--text:#e2e8f0;--muted:#94a3b8}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);padding:32px 16px}
.wrap{max-width:960px;margin:0 auto}
.header{background:linear-gradient(135deg,#1e3a8a,#0e7490);border-radius:16px;padding:32px;margin-bottom:24px}
.header h1{margin:0 0 8px;font-size:28px}
.header p{margin:4px 0;color:#dbeafe}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}
.kpi{background:var(--card);border-radius:12px;padding:20px}
.kpi .label{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.kpi .value{font-size:26px;font-weight:700;margin-top:6px}
.kpi .value.accent{color:var(--accent)}.kpi .value.green{color:var(--green)}.kpi .value.red{color:var(--red)}
.card{background:var(--card);border-radius:12px;padding:24px;margin-bottom:24px}
.card h2{margin-top:0;font-size:18px;border-bottom:1px solid #334155;padding-bottom:12px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #334155;font-size:14px}
th{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:11px;letter-spacing:.06em}
.bar{height:8px;background:#334155;border-radius:4px;overflow:hidden;min-width:120px}
.bar>div{height:100%;background:linear-gradient(90deg,#38bdf8,#818cf8)}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600}
.badge.ok{background:#064e3b;color:#6ee7b7}.badge.warn{background:#7c2d12;color:#fdba74}
.footer{color:var(--muted);font-size:12px;text-align:center;margin-top:32px}
"""


def render_html(summary: dict, client: str) -> str:
    e = _html.escape
    client_e = e(client)
    top = summary["top_services"]
    max_cost = max((s["cost"] for s in top), default=1) or 1

    def svc_rows() -> str:
        rows = []
        for s in top:
            w = s["cost"] / max_cost * 100
            rows.append(
                f"<tr><td>{e(s['service'])}</td>"
                f"<td><div class='bar'><div style='width:{w:.1f}%'></div></div></td>"
                f"<td>{_money(s['cost'])}</td><td>{_pct(s['share'])}</td></tr>"
            )
        return "\n".join(rows)

    def region_rows() -> str:
        return "\n".join(
            f"<tr><td>{e(r['region'])}</td><td>{_money(r['cost'])}</td></tr>"
            for r in summary["top_regions"]
        )

    def anomaly_rows() -> str:
        if not summary["anomalies"]:
            return "<tr><td colspan='3'><span class='badge ok'>None</span> — no anomalies detected.</td></tr>"
        return "\n".join(
            f"<tr><td>{e(a['date'])}</td><td>{_money(a['cost'])}</td>"
            f"<td>+{_money(a['deviation'])} vs daily avg</td></tr>"
            for a in summary["anomalies"]
        )

    region_card = ""
    if summary["top_regions"]:
        region_card = (
            "<div class='card'><h2>Top regions by spend</h2>"
            "<table><tr><th>Region</th><th>Spend</th></tr>"
            f"{region_rows()}</table></div>"
        )

    anom_class = "red" if summary["anomalies"] else "green"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FinOps Cost Report — {client_e}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>☁️ FinOps Cost Report</h1>
    <p><strong>{client_e}</strong></p>
    <p>Period {summary['date_from']} → {summary['date_to']} · {summary['days_covered']} days · {summary['row_count']} billing rows</p>
    <p>Generated {date.today().isoformat()}</p>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="label">Total spend</div><div class="value accent">{_money(summary['total_spend'])}</div></div>
    <div class="kpi"><div class="label">Daily average</div><div class="value">{_money(summary['daily_avg'])}</div></div>
    <div class="kpi"><div class="label">30-day forecast</div><div class="value green">{_money(summary['forecast_30d'])}</div></div>
    <div class="kpi"><div class="label">Anomalies (&gt;{summary['anomaly_threshold_std']}σ)</div><div class="value {anom_class}">{len(summary['anomalies'])}</div></div>
  </div>
  <div class="card">
    <h2>Top services by spend</h2>
    <table><tr><th>Service</th><th></th><th>Spend</th><th>Share</th></tr>
    {svc_rows()}
    </table>
  </div>
  {region_card}
  <div class="card">
    <h2>Anomaly detection</h2>
    <table><tr><th>Date</th><th>Spend</th><th>Deviation</th></tr>
    {anomaly_rows()}
    </table>
  </div>
  <div class="card">
    <h2>30-day forecast</h2>
    <p>Projected spend: <strong>{_money(summary['forecast_30d'])}</strong> — linear projection (daily average × 30).</p>
    <p style="color:var(--muted);font-size:13px">Method: daily spend grouped from the billing CSV; anomalies flagged where daily spend exceeds mean + N standard deviations.</p>
  </div>
  <div class="footer">Prepared by VisionQuantech · Cloud FinOps Cost Analyzer</div>
</div>
</body>
</html>
"""


def render(summary: dict, client: str, fmt: str) -> str:
    if fmt == "text":
        return render_text(summary, client)
    if fmt == "markdown":
        return render_markdown(summary, client)
    if fmt == "html":
        return render_html(summary, client)
    raise ValueError(f"unknown format: {fmt}")
