#!/usr/bin/env bash
set -euo pipefail
cd /root/benchmarks
exec /usr/bin/python3 -m benchmark_dashboard.server --host 172.18.0.1 --port 8766
