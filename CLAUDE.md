# Agent guide — benchmarks

> AGENTS.md and CLAUDE.md are byte-identical — same file for different harnesses. Edit AGENTS.md and copy to CLAUDE.md on every change. If a GEMINI.md exists, keep it identical as well.

## Project

**Benchmarks** — a small, practical benchmark dashboard for people who switch between LLMs and coding agents. See [`README.md`](README.md).

- **Tracks:** DeepSWE, AA Intelligence Index, GDPval-AA, AA Agentic Index, Terminal-Bench, BrowseComp, OSWorld-Verified, LongBench v2, LMArena + optional local-model tables. See [`README.md#what-it-tracks`](README.md#what-it-tracks) and [`docs/SOURCES.md`](docs/SOURCES.md).
- **Shape:** `benchmark_dashboard/` (sources, models, render, server, update), `data/benchmarks.json`, `public/index.html`, `scripts/`, `docs/`, `systemd/`, `tests/`.

## How it works (quick)

```
weekly timer -> fetch sources -> parse rows -> data/benchmarks.json -> render public/index.html -> optionally commit
```

Each parser returns `BenchmarkRow`; each collector returns `BenchmarkSnapshot` with `status` `ok`/`failed`. The updater refuses to overwrite a good dashboard if fewer than 3 sources succeed. See [`docs/SOURCES.md`](docs/SOURCES.md) for schema and per-source logic.

## How to run

```bash
pip install -r requirements.txt
python3 -m pytest -q
python3 -m benchmark_dashboard.update         # fetch + render (no commit)
python3 -m benchmark_dashboard.update --commit  # fetch + render + commit+push
python3 -m benchmark_dashboard.server --host 127.0.0.1 --port 8766
```

Helper scripts: [`scripts/update_and_commit.sh`](scripts/update_and_commit.sh), [`scripts/serve_local.sh`](scripts/serve_local.sh).

## Where source truth lives

- Parsers/collectors: [`benchmark_dashboard/sources.py`](benchmark_dashboard/sources.py)
- Schema: [`benchmark_dashboard/models.py`](benchmark_dashboard/models.py)
- Source map (authoritative for future maintenance): [`docs/SOURCES.md`](docs/SOURCES.md)
- Troubleshooting: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)

## Conventions

- British English in docs where relevant.
- Do not silently fabricate or backfill scores; mark failed sources as `failed`.
- Keep provenance visible in the UI.

## Private-setup notes

Some docs retain the original private self-hosted routing (Caddy/Authelia, `172.18.0.1`). Treat as reference; public adopters just need `python3 -m benchmark_dashboard.server` behind any static host. See [`docs/MAINTAINER-RUNBOOK.md`](docs/MAINTAINER-RUNBOOK.md) and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
