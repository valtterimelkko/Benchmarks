# Benchmark source and parser map

This document is for future agents maintaining `/root/benchmarks`. The most likely failure mode is an upstream site changing HTML/JS structure. Fix parsers in `benchmark_dashboard/sources.py`, then run `python3 -m pytest -q` and `python3 -m benchmark_dashboard.update`.

## Design principles

- Prefer official project sources where programmatically practical.
- Prefer difficult agentic benchmarks over generic model trivia/math marketing claims.
- Make provenance visible in the UI.
- Do not silently fabricate or backfill scores.
- Keep a previous good dashboard if most sources fail at once.

## Normalised row schema

Every parser returns `BenchmarkRow`:

```python
BenchmarkRow(
    rank=1,
    model="model/settings label",
    organization="OpenAI",
    score=70.05,
    score_unit="% solve rate",
    date="2026-05-15",       # optional
    metadata={...},           # benchmark-specific useful fields
)
```

Every source collector returns `BenchmarkSnapshot` with status `ok` or `failed`.

## Sources

### 1. DeepSWE

- Dashboard ID: `deep_swe`
- Primary source: `https://deepswe.datacurve.ai/`
- Methodology: `https://deepswe.datacurve.ai/blog`
- Fallback mirror: `https://benchlm.ai/benchmarks/deepSwe`
- Parser: `parse_deepswe_html()`

Logic:

- Fetch official Datacurve page.
- Parse embedded React/JS rows containing fields such as `model`, `harness`, `reasoning_effort`, `pass_rate`, `n_tasks_attempted`, `n_tasks_passed_any`, and `mean_cost_usd`.
- Convert `pass_rate` to percentage.
- If official rows are not found, parse BenchLM's `__NEXT_DATA__` leaderboard as a fallback.

Maintenance warning:

- The official page is not a simple HTML table. If Datacurve changes the client payload, update the regex or switch to a new official JSON endpoint if one appears.

### 2. Terminal-Bench

- Dashboard ID: `terminal_bench`
- Primary source: `https://www.tbench.ai/leaderboard/terminal-bench/2.1`
- Fallback source: `https://www.tbench.ai/leaderboard/terminal-bench/2.0`
- Parser: `parse_terminal_html()`

Logic:

- Parse the first HTML table.
- Expected columns: Rank, Agent, Model, Date, Agent Org, Model Org, Accuracy.
- If the 2.1 table has fewer than 5 rows, fetch 2.0 as a labelled fallback.

Maintenance warning:

- Terminal-Bench rows combine agent scaffold and model. Do not present this as pure model capability.

### 3. BrowseComp

- Dashboard ID: `browsecomp`
- Source used for rows: `https://benchlm.ai/benchmarks/browseComp`
- Original benchmark/methodology: `https://openai.com/index/browsecomp/`
- Parser: `parse_benchlm_next_data()`

Logic:

- BenchLM exposes benchmark-specific leaderboard rows inside `__NEXT_DATA__.props.pageProps.leaderboard`.
- This is a mirror rather than the original OpenAI leaderboard, so the UI and docs label it as such.

Maintenance warning:

- If BenchLM changes its Next.js data shape, either update `parse_benchlm_next_data()` or replace with another reliable BrowseComp leaderboard source.

### 4. OSWorld-Verified

- Dashboard ID: `osworld_verified`
- Source: `https://os-world.github.io/static/data/osworld_verified_results.xlsx`
- Project page: `https://os-world.github.io/`
- Parser: `parse_osworld_workbook()`

Logic:

- Download official XLSX.
- Read sheet `Eval Results`.
- Use numeric `Success rate` rows only, skipping pending rows such as `🚧`.
- Sort descending by success rate.

Maintenance warning:

- The workbook has many repeated variants (different max steps / approach settings). This is intentional; future work could add grouping by model if desired.

### 5. LongBench v2

- Dashboard ID: `longbench_v2`
- Source: `https://longbench2.github.io/`
- Project: `https://github.com/THUDM/LongBench`
- Parser: `parse_longbench_html()`

Logic:

- Parse the official table embedded in the HTML page.
- Use plain `Overall (%)` when present, otherwise use the adjacent `w/ CoT` overall score.
- Keep context window and parameter count in metadata.

Maintenance warning:

- LongBench is a useful long-context/document reasoning signal, but it is public and multiple-choice, so contamination risk is higher than with live agentic tasks.

### 6. LMArena Text Style Control

- Dashboard ID: `lmarena_text_style`
- Dataset: `https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset`
- API URL used: `https://datasets-server.huggingface.co/rows?dataset=lmarena-ai%2Fleaderboard-dataset&config=text_style_control&split=latest&offset=0&length=50`
- Parser: `parse_lmarena_rows()`

Logic:

- Fetch Hugging Face dataset-server rows.
- Use arena `rating` as score.
- Keep confidence bounds, votes, licence and category in metadata.

Maintenance warning:

- This is a writing/style preference proxy, not a rigorous academic-writing benchmark. It should not be used to judge citation accuracy or factuality.

## Adding or replacing a benchmark

1. Add a parser function with unit tests in `tests/test_sources.py`.
2. Add a `collect_*()` function returning `BenchmarkSnapshot`.
3. Add the collector to `collect_all()`.
4. Update `README.md` and this file.
5. Run:

```bash
python3 -m pytest -q
python3 -m benchmark_dashboard.update
```

6. Inspect `public/index.html` and `data/benchmarks.json`.
