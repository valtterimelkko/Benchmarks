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

### 2. GDPval-AA

- Dashboard ID: `gdpval_aa`
- Source used for rows: `https://benchlm.ai/benchmarks/gdpvalAa`
- Original benchmark/methodology: `https://openai.com/index/gdpval/`
- Parser: `parse_benchlm_next_data()` with `score_unit="Elo rating"`

Logic:

- BenchLM exposes benchmark-specific leaderboard rows inside `__NEXT_DATA__.props.pageProps.leaderboard`.
- GDPval-AA uses Elo ratings from head-to-head comparisons evaluated by Artificial Analysis.
- 1,320 tasks created by professionals (average 14 years experience) across 44 occupations and 9 industries.
- 114 models evaluated as of June 2026.

Authenticity note:

- Tasks were created by OpenAI, but scoring is done independently by Artificial Analysis via head-to-head Elo battles. This differs from AA-LCR (rejected earlier) which had estimated/cross-referenced scores. GDPval-AA Elo ratings come from actual model-vs-model comparisons.

Maintenance warning:

- If BenchLM changes its Next.js data shape, update `parse_benchlm_next_data()` or replace with the Artificial Analysis direct source at `artificialanalysis.ai/evaluations/gdpval-aa`.

### 3. Terminal-Bench

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

### 4. BrowseComp

- Dashboard ID: `browsecomp`
- Source used for rows: `https://benchlm.ai/benchmarks/browseComp`
- Original benchmark/methodology: `https://openai.com/index/browsecomp/`
- Parser: `parse_benchlm_next_data()`

Logic:

- BenchLM exposes benchmark-specific leaderboard rows inside `__NEXT_DATA__.props.pageProps.leaderboard`.
- This is a mirror rather than the original OpenAI leaderboard, so the UI and docs label it as such.

Maintenance warning:

- If BenchLM changes its Next.js data shape, either update `parse_benchlm_next_data()` or replace with another reliable BrowseComp leaderboard source.

### 5. OSWorld-Verified

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

### 6. LongBench v2

- Dashboard ID: `longbench_v2`
- Primary source: `https://longbench2.github.io/`
- Original benchmark paper: `https://arxiv.org/abs/2412.15204`
- Fallback mirror: `https://benchlm.ai/benchmarks/longBenchV2`
- Parser: `parse_longbench_html()` for official site; `parse_benchlm_next_data()` as fallback

Logic:

- Fetch the official LongBench v2 project site and parse its HTML leaderboard table.
- LongBench v2 tests whether models can use extended context windows for reasoning and retrieval. 38 models from the official leaderboard as of June 2026 (Gemini-2.5-Pro, Qwen3-235B, DeepSeek-R1, etc.).
- Switching to the official source fixed staleness: the BenchLM mirror had only 11 models and showed Claude Opus 4.5 at the top, while the official site has current frontier models.
- "Human" baseline row is filtered out.
- Replaced AA-LCR earlier, which had questionable data quality (117 estimated/cross-referenced scores from Artificial Analysis, many rankings contradicted by the official source).

Maintenance warning:

- The official site uses a static HTML table that BeautifulSoup can parse. If the table structure changes, update `parse_longbench_html()` and check column index mappings (cells[1]=model, cells[2]=params, cells[3]=context, cells[4]=date, cells[5]=overall, cells[6]=w/CoT).

### 7. LMArena Text Style Control

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

### 8. Artificial Analysis Intelligence Index

- Dashboard ID: `aa_intelligence_index`
- Source used for rows: `https://artificialanalysis.ai/` (homepage)
- Methodology: `https://artificialanalysis.ai/methodology/intelligence-benchmarking`
- Parser: `parse_aa_intelligence_index_ldjson()`

Logic:

- Fetch the Artificial Analysis homepage.
- It embeds multiple `<script type="application/ld+json">` schema.org `Dataset` blocks.
- Use the dataset named exactly `Artificial Analysis Intelligence Index` (score key `intelligenceIndex`).
- Fallback: the shorter `Intelligence` dataset (score key `artificialAnalysisIntelligenceIndex`) from the same page if AA renames the headline block.
- Exact name matching matters: `Artificial Analysis Intelligence Index by Open Weights / Proprietary` is a different cut and must not be parsed.
- Sort descending by score, assign ranks, round to 1 decimal, make `detailsUrl` absolute, extract the index version (e.g. `v4.1`) from the dataset description into row metadata.
- Organisation is inferred from the model label via `infer_org()`; genuinely unknown orgs (e.g. new labs) render as `Unknown` rather than being guessed.

Maintenance warning:

- The JSON-LD blocks are AA's own machine-readable export and quite stable, but if rows disappear, check whether the dataset `name` or score key changed (`grep -o 'intelligenceIndex[^,}]*'` on the saved HTML). The component evaluations (and the index version) change over time — the description text in `collect_aa_intelligence_index()` may need refreshing when AA bumps the version.

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
7. Browser-level acceptance tests live in `tests/test_playwright_dashboard.py` (real Chromium via Playwright against the served artifact; skips cleanly when Playwright is unavailable).
