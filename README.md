# Benchmarks

A small, practical benchmark dashboard for people who regularly switch between LLMs and coding agents.

This project started from a very specific frustration: repeatedly doing ad hoc searches like _"which model is best on this benchmark now?"_ and then trying to translate generic leaderboard results into real work decisions. The goal here is to keep one page that updates weekly and tracks the benchmark families that are most relevant to hands-on agent use rather than abstract prestige alone.

## Why this exists

I use AI systems across several recurring workflows:

- coding agents working over real repositories
- terminal and CLI-heavy tool use
- browser research and web navigation
- desktop / computer-use tasks
- long-context reading and summarisation
- writing and style-sensitive drafting

Most public leaderboard summaries flatten these into one vague notion of “best model”. This dashboard takes a different approach:

- it focuses on a small set of benchmarks that map more closely to real tasks
- it keeps source caveats visible
- it updates automatically on a schedule
- it produces a static artifact that others can fork, adapt, or extend

If your workflow looks similar, you can use this repo as-is. If not, it is meant to be easy to fork and reshape around your own benchmark mix.

## What it tracks

The current dashboard includes:

1. **DeepSWE** — long-horizon software engineering agents
2. **AA Intelligence Index** — Artificial Analysis' composite of 9 independently-run evaluations (reasoning, knowledge, agentic, coding, long-context)
3. **GDPval-AA** — agentic professional work across real deliverables
4. **Terminal-Bench** — shell, terminal, and tool-use tasks
5. **BrowseComp** — browser/web research tasks
6. **OSWorld-Verified** — desktop/computer-use agents
7. **LongBench v2** — long-context retrieval and reasoning
8. **LMArena Text Style Control** — human preference proxy for writing/style

These were chosen because they say more about the kinds of work I actually do than the most easily optimised headline benchmarks.

## Repository structure

```text
benchmark_dashboard/   Python package for fetching, parsing, and rendering
data/                  Normalised benchmark snapshot JSON
public/                Rendered static dashboard
systemd/               Example service and timer units
docs/                  Sources, deployment notes, troubleshooting, maintainer docs
scripts/               Small helper scripts
tests/                 Parser/render regression tests
```

## How it works

```text
weekly timer
  -> fetch benchmark sources
  -> parse and normalise rows
  -> write data/benchmarks.json
  -> render public/index.html
  -> optionally commit updated snapshots
```

The output is a simple static dashboard, so the repo is easy to self-host behind any static web server.

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python3 -m pytest -q
```

Fetch sources and rebuild the dashboard once:

```bash
python3 -m benchmark_dashboard.update
```

Serve the generated site locally:

```bash
python3 -m benchmark_dashboard.server --host 127.0.0.1 --port 8766
```

## Documentation map

- [`docs/SOURCES.md`](docs/SOURCES.md) — where each benchmark comes from and how parsing works
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — common parser/source failures
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — example deployment notes
- [`docs/MAINTAINER-RUNBOOK.md`](docs/MAINTAINER-RUNBOOK.md) — maintainer-oriented operational notes from the original private setup

## Notes for public users

This repository was originally built for a private self-hosted setup, so some docs still include environment-specific examples. Those are best treated as implementation references rather than required architecture.

## License

MIT
