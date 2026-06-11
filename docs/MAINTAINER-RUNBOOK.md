# Maintainer Runbook

This document preserves the original maintainer-facing operational notes for the benchmark dashboard.

Use the public [`../README.md`](../README.md) for project overview and adoption. Use this file when maintaining the original self-hosted deployment shape.

## Original deployment shape

The dashboard was deployed locally behind an existing Caddy + Authelia setup rather than on a public static host.

Key local details from the original setup:

- internal container URL: `http://benchmarks-dashboard:8766`
- local repo path: `/root/benchmarks`
- snapshots committed back to GitHub on update
- static serving done from a small container on the same Docker network as Caddy

This was chosen because it fit an existing private infrastructure setup and avoided exposing a host port directly.

## Core commands

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

Serve locally for testing:

```bash
cd /root/benchmarks
python3 -m benchmark_dashboard.server --host 127.0.0.1 --port 8766
```

## Systemd units used in the original setup

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

## Original routing notes

The original deployment sat behind Caddy and Authelia and did not publish a host port. That detail is not required for public adopters, but it explains why some deployment docs are infrastructure-specific.

## Operational caution

If you are working inside a live remote agent environment, avoid restarting shared reverse proxies without explicit approval.

## Robustness behaviour

The updater refuses to overwrite an existing dashboard if fewer than three benchmark sources succeed. This protects against broad upstream outages or parser breakage replacing a good dashboard with mostly empty output.
