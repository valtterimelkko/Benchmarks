# Benchmarks — private LLM/agent benchmark dashboard

This repository powers the private benchmark dashboard at:

- Planned public URL behind Authelia/Caddy: `https://benchmarks.letsautomate.work`
- Internal service URL from the Caddy container: `http://benchmarks-dashboard:8766`
- Local files: `/root/benchmarks`

The dashboard exists to help Valtteri choose which LLM model to use for practical agent work: coding, custom CLI generation, terminal/tool use, browser research, computer use, long-context reading/summarisation, and writing.

It deliberately avoids a single fake “best model” score. Instead, it shows a small set of benchmarks that map to real work patterns and keeps source/update caveats visible.

## Core benchmark set

1. **DeepSWE** — long-horizon software engineering agents.
2. **GDPval-AA** — agentic professional work across 44 occupations (1,320 real deliverables, Elo-scored by Artificial Analysis).
3. **Terminal-Bench** — terminal, shell, CLI and tool-use tasks.
4. **BrowseComp** — browser/web research tasks.
5. **OSWorld-Verified** — desktop/computer-use agents.
6. **LongBench v2** — long-context reasoning and retrieval (38 models from official leaderboard).
7. **LMArena Text Style Control** — human preference proxy for prose/style quality.

See [`docs/SOURCES.md`](docs/SOURCES.md) for source URLs and parser logic.

## How it works

```text
systemd timer (weekly)
  -> python -m benchmark_dashboard.update --commit
       -> fetch benchmark sources
       -> parse into normalised rows
       -> write data/benchmarks.json
       -> render public/index.html
       -> commit + push changed snapshot files

systemd server (persistent)
  -> docker run caddy:latest caddy file-server --listen :8766 --root /srv
       -> container joins n8n-docker-caddy_default as benchmarks-dashboard
       -> main Caddy container reverse-proxies to http://benchmarks-dashboard:8766
       -> Authelia protects the subdomain
```

The dashboard server does **not** publish a host port. It is only reachable on the internal Docker network used by Caddy, which avoids direct public exposure and avoids host firewall issues.

## Important operational constraint

**Do not restart Caddy from an agent session unless explicitly approved.** Reloading/restarting Caddy can interrupt active access to Pi. This repo includes Caddy configuration instructions, but Caddy should be restarted or reloaded manually by the user.

## Commands

Run tests:

```bash
cd /root/benchmarks
python3 -m pytest -q
```

Fetch and render once without git commit:

```bash
cd /root/benchmarks
python3 -m benchmark_dashboard.update
```

Fetch, render, commit and push if changed:

```bash
cd /root/benchmarks
python3 -m benchmark_dashboard.update --commit
```

Serve locally for testing without systemd, if needed:

```bash
cd /root/benchmarks
python3 -m benchmark_dashboard.server --host 127.0.0.1 --port 8766
```

From the Caddy container, check the systemd-managed container:

```bash
docker exec n8n-docker-caddy-caddy-1 curl -fsS http://benchmarks-dashboard:8766/ | grep 'LLM Agent Benchmark Dashboard'
```

## Systemd units

Installed units should be:

- `/etc/systemd/system/benchmarks-dashboard.service`
- `/etc/systemd/system/benchmarks-dashboard-update.service`
- `/etc/systemd/system/benchmarks-dashboard-update.timer`

Check status:

```bash
systemctl status benchmarks-dashboard.service
systemctl status benchmarks-dashboard-update.timer
systemctl list-timers benchmarks-dashboard-update.timer
```

View logs:

```bash
journalctl -u benchmarks-dashboard.service -n 100 --no-pager
journalctl -u benchmarks-dashboard-update.service -n 100 --no-pager
```

## Robustness behaviour

The updater refuses to overwrite an existing dashboard if fewer than three benchmark sources succeed. This prevents a broad network outage or upstream HTML change from replacing a good dashboard with mostly failed cards.

Individual benchmark failures are still shown when enough other sources succeed, so parser/source breakage is visible.

## Repository and backup

This folder is a git repository and is pushed to the private GitHub repo `valtterimelkko/Benchmarks`. Weekly update commits include `data/benchmarks.json` and `public/index.html` when they change.

Do not commit secrets, credentials, raw cache dumps, or `.herenow/state.json`. See `.gitignore`.
