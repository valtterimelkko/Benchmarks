import json
from pathlib import Path

from benchmark_dashboard.models import BenchmarkRow, BenchmarkSnapshot, DashboardData
from benchmark_dashboard.render import render_dashboard
from benchmark_dashboard.update import atomic_write_json, is_usable_snapshot, should_commit


def sample_dashboard():
    return DashboardData(
        generated_at="2026-06-08T12:00:00Z",
        benchmarks=[
            BenchmarkSnapshot(
                id="deep_swe",
                name="DeepSWE",
                category="Coding agents",
                description="Long-horizon software engineering tasks",
                source_url="https://deepswe.datacurve.ai/",
                methodology_url="https://deepswe.datacurve.ai/blog",
                authenticity="Original tasks with behaviour verifiers; lower contamination risk than issue-derived sets.",
                update_strategy="Official HTML parse with BenchLM mirror fallback.",
                fetched_at="2026-06-08T12:00:00Z",
                status="ok",
                rows=[BenchmarkRow(rank=1, model="gpt-5-5 [xhigh]", organization="OpenAI", score=70.05, score_unit="% solve rate")],
            )
        ],
    )


def test_render_dashboard_contains_intent_sources_and_rows():
    html = render_dashboard(sample_dashboard())
    assert "LLM Agent Benchmark Dashboard" in html
    assert "DeepSWE" in html
    assert "gpt-5-5 [xhigh]" in html
    assert "Original tasks with behaviour verifiers" in html
    assert "Generated 2026-06-08T12:00:00Z" in html


def test_render_dashboard_leader_line_spacing_by_unit():
    # %-units attach directly to the number; word units get a separating space.
    assert "70.05% solve rate" in render_dashboard(sample_dashboard())
    elo_dashboard = sample_dashboard()
    elo_dashboard.benchmarks[0].rows[0].score = 59.9
    elo_dashboard.benchmarks[0].rows[0].score_unit = "index points"
    assert "59.9 index points" in render_dashboard(elo_dashboard)


def test_is_usable_snapshot_requires_enough_successful_sources():
    good = sample_dashboard()
    assert is_usable_snapshot(good, minimum_ok=1) is True
    bad = DashboardData(
        generated_at="2026-06-08T12:00:00Z",
        benchmarks=[
            BenchmarkSnapshot(
                id="broken",
                name="Broken",
                category="Test",
                description="",
                source_url="https://example.com",
                methodology_url=None,
                authenticity="",
                update_strategy="",
                fetched_at="2026-06-08T12:00:00Z",
                status="failed",
                rows=[],
            )
        ],
    )
    assert is_usable_snapshot(bad, minimum_ok=1) is False


def test_atomic_write_json_is_stable_and_creates_parent(tmp_path):
    target = tmp_path / "nested" / "data.json"
    atomic_write_json(target, {"b": 2, "a": 1})
    assert target.exists()
    assert target.read_text().startswith("{\n  \"a\": 1")
    assert json.loads(target.read_text()) == {"a": 1, "b": 2}


def test_should_commit_detects_changed_tracked_content(tmp_path):
    import subprocess

    repo = tmp_path
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=repo, check=True)
    target = repo / "data.txt"
    target.write_text("old")
    subprocess.run(["git", "add", "data.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
    target.write_text("new")
    assert should_commit(repo, [target]) is True
    assert should_commit(repo, [repo / "missing.txt"]) is False
