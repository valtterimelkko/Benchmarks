# Troubleshooting

## Dashboard page is stale

1. Check timer status:

```bash
systemctl list-timers benchmarks-dashboard-update.timer
systemctl status benchmarks-dashboard-update.timer
```

2. Run the updater manually without commit:

```bash
cd /root/benchmarks
python3 -m benchmark_dashboard.update
```

3. If successful, run with commit:

```bash
python3 -m benchmark_dashboard.update --commit
```

## Most sources failed and updater refused to overwrite

This is intentional. The updater raises:

```text
Refusing to overwrite existing dashboard because fewer than 3 benchmark sources succeeded
```

This protects the last good dashboard from broad network failures or major upstream site changes.

Actions:

1. Check whether this is a network/DNS issue:

```bash
curl -I https://deepswe.datacurve.ai/
curl -I https://www.tbench.ai/leaderboard/terminal-bench/2.1
```

2. Check individual parser/source logic in `benchmark_dashboard/sources.py`.
3. Update unit tests in `tests/test_sources.py` before changing parser code.
4. Run tests and updater again.

## One source failed

Open `data/benchmarks.json` and find the benchmark with `"status": "failed"`. The `error` field should show the exception. The rendered dashboard also shows source-specific errors inside the benchmark card.

Common causes:

- HTML table columns changed.
- Next.js `__NEXT_DATA__` structure changed.
- Hugging Face dataset-server timed out.
- OSWorld moved or renamed the XLSX file.

## Site service is not reachable

Check the systemd-managed container:

```bash
systemctl status benchmarks-dashboard.service
journalctl -u benchmarks-dashboard.service -n 100 --no-pager
docker ps --filter name=benchmarks-dashboard
```

Expected route from the main Caddy container:

```text
http://benchmarks-dashboard:8766
```

Check from Caddy container:

```bash
docker exec n8n-docker-caddy-caddy-1 curl -fsS http://benchmarks-dashboard:8766/ | grep 'LLM Agent Benchmark Dashboard'
```

If this fails, confirm the dashboard container is attached to `n8n-docker-caddy_default`:

```bash
docker inspect benchmarks-dashboard --format '{{json .NetworkSettings.Networks}}'
```

## Caddy route not live

The agent deliberately does not restart Caddy. After manual reload/restart, validate:

```bash
curl -I https://benchmarks.letsautomate.work
```

If Authelia redirects to login, routing is probably working.

Before manual reload, validate config syntax:

```bash
docker exec n8n-docker-caddy-caddy-1 caddy validate --config /etc/caddy/Caddyfile
```

## Weekly git push failed

Check update service logs:

```bash
journalctl -u benchmarks-dashboard-update.service -n 200 --no-pager
```

Common causes:

- GitHub SSH/auth issue.
- Remote repo renamed or unavailable.
- Network issue.
- Generated files changed but git user config missing.

Check:

```bash
cd /root/benchmarks
git remote -v
git status --short
gh auth status
ssh -T git@github.com
```

## Adding parser fixes safely

1. Write or update a failing test in `tests/test_sources.py` with a small fixture for the new upstream shape.
2. Run `python3 -m pytest -q` and confirm it fails for the expected reason.
3. Fix `benchmark_dashboard/sources.py`.
4. Run tests and `python3 -m benchmark_dashboard.update`.
5. Commit and push.
