# Deployment and routing

## Current deployment choice

The dashboard is deployed locally behind the existing Caddy + Authelia setup, rather than on here.now.

Reasoning:

- The dashboard is private and personal.
- The machine already has Authelia SSO for `*.letsautomate.work`.
- The updater runs locally and commits snapshots to GitHub.
- Keeping data generation and serving on the same host is simpler and easier to repair.

here.now remains a possible future static mirror, but it would add a second hosting/auth surface for a private internal dashboard.

## Port and Docker network

- Internal container port: `8766`
- Container name: `benchmarks-dashboard`
- Docker network: `n8n-docker-caddy_default`
- Public host port: **none**

Why a same-network container instead of a host port:

- Existing Caddy entries use mixed host routing (`172.18.0.1`, `host.docker.internal`) and have had routing challenges before.
- During build testing, newly bound host ports on `172.18.0.1` were reachable from the host but timed out from the Caddy container, while existing long-running host services behaved differently.
- Running the static dashboard in a small `caddy:latest` container on the same Docker network as the main Caddy container gives the most reliable internal route: `http://benchmarks-dashboard:8766`.
- No host port is published, so there is no direct public exposure and no UFW allow rule is needed.

Validate from host:

```bash
docker ps --filter name=benchmarks-dashboard
```

Validate from Caddy container:

```bash
docker exec n8n-docker-caddy-caddy-1 curl -fsS http://benchmarks-dashboard:8766/ | grep 'LLM Agent Benchmark Dashboard'
```

## Firewall note

At build time, `ufw` was not installed (`ufw: command not found`). The dashboard container publishes no host port. If a future firewall is added, it should not need any public rule for this dashboard.

## Caddy configuration

Caddy config lives at:

```text
/root/n8n-docker-caddy/caddy_config/Caddyfile
```

The dashboard entry should follow the same Authelia forward-auth pattern as the other services, but reverse-proxy to the same-network dashboard container:

```caddyfile
benchmarks.letsautomate.work {
    log default
    reverse_proxy authelia:9091 {
        method GET
        rewrite /api/authz/forward-auth
        header_up -Authorization
        header_up X-Forwarded-Method {method}
        header_up X-Forwarded-Uri {uri}
        header_up X-Forwarded-Host {host}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Forwarded-For {remote_host}
        @auth_ok status 2xx
        handle_response @auth_ok {
        }
    }
    reverse_proxy benchmarks-dashboard:8766 {
        header_up -Authorization
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Forwarded-Host {host}
    }
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        -Server
    }
}
```

Do **not** restart Caddy from an agent session. After config changes, the user can manually restart/reload Caddy.

Safe validation without reload:

```bash
docker exec n8n-docker-caddy-caddy-1 caddy validate --config /etc/caddy/Caddyfile
```

## Cache behaviour

The container sends `Cache-Control: no-cache` (see `deploy/Caddyfile`). If a user still sees a stale dashboard, one hard refresh (Ctrl+Shift+R / Cmd+Shift+R) replaces the cached copy; afterwards every visit revalidates automatically.

## Landing page

Landing source:

```text
/root/landing/index.html
```

Served copy:

```text
/var/www/landing/index.html
```

Both should contain a card for `https://benchmarks.letsautomate.work`.

## Systemd

Server service:

```bash
systemctl status benchmarks-dashboard.service
```

Updater timer:

```bash
systemctl status benchmarks-dashboard-update.timer
systemctl list-timers benchmarks-dashboard-update.timer
```

The timer uses `Persistent=true`, so missed weekly runs execute after boot when the machine has been offline.
