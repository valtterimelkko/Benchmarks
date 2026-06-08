from __future__ import annotations

import html
import json
from collections import Counter

from .models import DashboardData


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _row_metadata(metadata: dict) -> str:
    interesting = []
    for key in ["agent", "harness", "reasoning_effort", "context", "max_steps", "votes", "source_type", "success_total"]:
        value = metadata.get(key)
        if value not in (None, "", []):
            interesting.append(f"{key.replace('_', ' ')}: {value}")
    return " · ".join(interesting)


def render_dashboard(data: DashboardData) -> str:
    ok_count = sum(1 for benchmark in data.benchmarks if benchmark.status == "ok")
    status_counts = Counter(benchmark.status for benchmark in data.benchmarks)
    cards = []
    for benchmark in data.benchmarks:
        top = benchmark.rows[0] if benchmark.rows else None
        status_class = f"status-{benchmark.status}"
        rows_html = "".join(
            f"""
            <tr>
              <td class="rank">{row.rank}</td>
              <td><strong>{_esc(row.model)}</strong><span>{_esc(row.organization or 'Unknown')}</span></td>
              <td class="score">{row.score:g}<small>{_esc(row.score_unit)}</small></td>
              <td>{_esc(row.date or '—')}</td>
              <td class="meta">{_esc(_row_metadata(row.metadata))}</td>
            </tr>
            """
            for row in benchmark.rows
        )
        if not rows_html:
            rows_html = f"<tr><td colspan='5' class='error'>{_esc(benchmark.error or 'No rows available')}</td></tr>"
        top_html = "No data"
        if top:
            top_html = f"{_esc(top.model)} <span>{top.score:g}{_esc(top.score_unit.replace('% ', '% '))}</span>"
        cards.append(
            f"""
            <section class="benchmark-card" id="{_esc(benchmark.id)}">
              <div class="card-head">
                <div>
                  <p class="category">{_esc(benchmark.category)}</p>
                  <h2>{_esc(benchmark.name)}</h2>
                </div>
                <span class="status {status_class}">{_esc(benchmark.status)}</span>
              </div>
              <p class="description">{_esc(benchmark.description)}</p>
              <div class="leader"><span>Current leader</span><strong>{top_html}</strong></div>
              <details>
                <summary>Why this benchmark is here</summary>
                <p><strong>Authenticity:</strong> {_esc(benchmark.authenticity)}</p>
                <p><strong>Update logic:</strong> {_esc(benchmark.update_strategy)}</p>
                {f'<p class="warning"><strong>Warning:</strong> {_esc(benchmark.warning)}</p>' if benchmark.warning else ''}
                {f'<p class="error"><strong>Error:</strong> {_esc(benchmark.error)}</p>' if benchmark.error else ''}
                <p><a href="{_esc(benchmark.source_url)}" target="_blank" rel="noopener noreferrer">Source</a>{' · <a href="' + _esc(benchmark.methodology_url) + '" target="_blank" rel="noopener noreferrer">Methodology</a>' if benchmark.methodology_url else ''}</p>
              </details>
              <div class="table-wrap">
                <table>
                  <thead><tr><th>#</th><th>Model</th><th>Score</th><th>Date</th><th>Notes</th></tr></thead>
                  <tbody>{rows_html}</tbody>
                </table>
              </div>
            </section>
            """
        )

    notes_html = "".join(f"<li>{_esc(note)}</li>" for note in data.notes)
    embedded_json = json.dumps(data.to_dict(), ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LLM Agent Benchmark Dashboard</title>
<style>
:root {{ color-scheme: dark; --bg:#111113; --surface:#1a1a1f; --surface2:#22232a; --text:#eee8df; --muted:#a59d92; --line:rgba(255,255,255,.08); --accent:#d48a5a; --good:#79d18b; --bad:#ff7a7a; --warn:#f2bf65; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:radial-gradient(circle at top left,#2b211d 0,#111113 38rem); color:var(--text); }}
a {{ color:var(--accent); }}
header {{ max-width:1180px; margin:0 auto; padding:56px 22px 28px; }}
h1 {{ font-family:Georgia,serif; font-weight:400; letter-spacing:-.04em; font-size:clamp(2.3rem,6vw,5rem); line-height:.94; margin:0 0 18px; }}
header p {{ color:var(--muted); max-width:780px; line-height:1.6; font-size:1.03rem; }}
.summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; margin-top:28px; }}
.summary div {{ background:rgba(255,255,255,.045); border:1px solid var(--line); border-radius:18px; padding:18px; }}
.summary span {{ display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }}
.summary strong {{ display:block; margin-top:8px; font-size:1.5rem; }}
main {{ max-width:1180px; margin:0 auto; padding:10px 22px 64px; display:grid; gap:18px; }}
.benchmark-card {{ background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.025)); border:1px solid var(--line); border-radius:24px; padding:22px; box-shadow:0 24px 80px rgba(0,0,0,.22); }}
.card-head {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }}
.category {{ color:var(--accent); margin:0 0 6px; text-transform:uppercase; letter-spacing:.1em; font-size:.74rem; font-weight:700; }}
h2 {{ margin:0; font-size:1.55rem; letter-spacing:-.02em; }}
.status {{ border:1px solid var(--line); border-radius:999px; padding:6px 10px; font-size:.75rem; text-transform:uppercase; letter-spacing:.08em; }}
.status-ok {{ color:var(--good); }} .status-failed {{ color:var(--bad); }} .status-partial {{ color:var(--warn); }}
.description {{ color:var(--muted); line-height:1.55; max-width:850px; }}
.leader {{ margin:16px 0; padding:16px; border-radius:18px; background:rgba(212,138,90,.09); border:1px solid rgba(212,138,90,.22); }}
.leader span {{ display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; margin-bottom:5px; }}
.leader strong {{ font-size:1.05rem; }} .leader strong span {{ display:inline; color:var(--accent); margin-left:8px; font-size:inherit; letter-spacing:normal; text-transform:none; }}
details {{ margin:12px 0 16px; color:var(--muted); }} summary {{ cursor:pointer; color:var(--text); }}
.table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:18px; }}
table {{ width:100%; border-collapse:collapse; min-width:780px; }}
th,td {{ padding:12px 14px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} th {{ color:var(--muted); font-size:.76rem; text-transform:uppercase; letter-spacing:.08em; background:rgba(255,255,255,.03); }}
td.rank {{ color:var(--accent); font-variant-numeric:tabular-nums; width:56px; }}
td strong {{ display:block; }} td span, .meta {{ color:var(--muted); font-size:.86rem; }}
.score {{ font-variant-numeric:tabular-nums; font-weight:700; }} .score small {{ display:block; color:var(--muted); font-weight:400; }}
.error {{ color:var(--bad); }} .warning {{ color:var(--warn); }}
footer {{ max-width:1180px; margin:0 auto; color:var(--muted); padding:0 22px 38px; font-size:.85rem; }}
@media (max-width:760px) {{ header {{ padding-top:34px; }} .benchmark-card {{ padding:16px; }} }}
</style>
</head>
<body>
<header>
  <h1>LLM Agent Benchmark Dashboard</h1>
  <p>A private weekly snapshot of benchmarks that matter for practical agent work: coding, terminal/CLI use, browser research, computer use, long-context reading, and writing quality. This page intentionally favours hard-to-game agentic benchmarks over generic marketing scores.</p>
  <div class="summary">
    <div><span>Generated</span><strong>{_esc(data.generated_at)}</strong></div>
    <div><span>Sources OK</span><strong>{ok_count}/{len(data.benchmarks)}</strong></div>
    <div><span>Failed</span><strong>{status_counts.get('failed', 0)}</strong></div>
    <div><span>Refresh</span><strong>Weekly</strong></div>
  </div>
</header>
<main>
  {''.join(cards)}
  <section class="benchmark-card">
    <h2>Operating notes</h2>
    <ul>{notes_html}</ul>
  </section>
</main>
<footer>
  Generated {_esc(data.generated_at)} · Protected by Authelia/Caddy · Snapshot JSON embedded for debugging.
</footer>
<script id="benchmark-data" type="application/json">{embedded_json}</script>
</body>
</html>
"""
