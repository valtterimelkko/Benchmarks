from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .models import DashboardData
from .render import render_dashboard
from .sources import collect_all, now_iso

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "benchmarks.json"
PUBLIC_PATH = ROOT / "public" / "index.html"

DEFAULT_NOTES = [
    "If a source parser fails, the dashboard marks that benchmark as failed rather than silently fabricating data.",
    "Public benchmark rows often combine model + scaffold + settings. Treat them as model-selection signals, not absolute truth.",
    "DeepSWE, Terminal-Bench, BrowseComp and OSWorld are the strongest fits for day-to-day agent/tool-use choices; LongBench v2 and LMArena are supporting signals for long-context and writing tasks.",
]


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def atomic_write_json(path: Path, payload: dict) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=check)


def should_commit(repo: Path, paths: list[Path]) -> bool:
    existing = [str(path.relative_to(repo)) for path in paths if path.exists()]
    if not existing:
        return False
    result = run_git(repo, ["status", "--porcelain", "--", *existing], check=False)
    return bool(result.stdout.strip())


def commit_and_push(repo: Path, paths: list[Path], message: str) -> bool:
    existing = [str(path.relative_to(repo)) for path in paths if path.exists()]
    if not existing:
        return False
    run_git(repo, ["add", *existing])
    if not should_commit(repo, paths):
        return False
    run_git(repo, ["commit", "-m", message])
    run_git(repo, ["push"])
    return True


def build_dashboard() -> DashboardData:
    return DashboardData(generated_at=now_iso(), benchmarks=collect_all(), notes=DEFAULT_NOTES)


def is_usable_snapshot(data: DashboardData, minimum_ok: int = 3) -> bool:
    return sum(1 for benchmark in data.benchmarks if benchmark.status == "ok" and benchmark.rows) >= minimum_ok


def update_files(commit: bool = False) -> DashboardData:
    data = build_dashboard()
    if not is_usable_snapshot(data) and DATA_PATH.exists() and PUBLIC_PATH.exists():
        # Preserve the last good dashboard if a transient network or upstream outage breaks most sources.
        raise RuntimeError("Refusing to overwrite existing dashboard because fewer than 3 benchmark sources succeeded")
    atomic_write_json(DATA_PATH, data.to_dict())
    atomic_write_text(PUBLIC_PATH, render_dashboard(data))
    if commit:
        changed = commit_and_push(ROOT, [DATA_PATH, PUBLIC_PATH], f"chore: update benchmark snapshot {data.generated_at}")
        print(f"git_commit={'yes' if changed else 'no_changes'}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch benchmark data and render the private dashboard.")
    parser.add_argument("--commit", action="store_true", help="Commit and push data/public changes if git is configured.")
    args = parser.parse_args()
    data = update_files(commit=args.commit)
    ok = sum(1 for benchmark in data.benchmarks if benchmark.status == "ok")
    print(f"generated_at={data.generated_at} sources_ok={ok}/{len(data.benchmarks)} data={DATA_PATH} html={PUBLIC_PATH}")


if __name__ == "__main__":
    main()
