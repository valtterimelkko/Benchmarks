#!/usr/bin/env bash
set -euo pipefail
cd /root/benchmarks
/usr/bin/python3 -m benchmark_dashboard.update --commit
