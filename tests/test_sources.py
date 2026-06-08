import io
import json
from unittest.mock import MagicMock, patch

import openpyxl
import pytest

from benchmark_dashboard.models import BenchmarkRow
from benchmark_dashboard.sources import (
    _fetch_with_retry,
    _find_col,
    _validate_snapshot,
    parse_benchlm_next_data,
    parse_deepswe_html,
    parse_longbench_html,
    parse_lmarena_rows,
    parse_osworld_workbook,
    parse_terminal_html,
)


def test_parse_deepswe_official_react_payload():
    html = '''rows:$R[246]=[$R[247]={model:"gpt-5-5",harness:"mini-swe-agent",reasoning_effort:"xhigh",config:"mini_swe_agent_gpt_5_5_xhigh",source:"deep-swe",pass_rate:0.7004504504504504,pass_at_1:0.7004504504504504,pass_at_4:0.8828828828828829,n_passed:311,n_attempted:444,n_tasks_attempted:111,n_tasks_passed_any:98,ci_passed:311,ci_attempted:444,ci_lo:0.67,ci_hi:0.72,ci_half:0.028,n_runs:4,mean_cost_usd:6.60},$R[248]={model:"kimi-k2-6",harness:"mini-swe-agent",reasoning_effort:"medium",config:"mini_swe_agent_kimi",source:"deep-swe",pass_rate:0.2400,n_tasks_attempted:113,n_tasks_passed_any:27,mean_cost_usd:0.42}]'''
    rows = parse_deepswe_html(html)
    assert rows[0].model == "gpt-5-5 [xhigh]"
    assert rows[0].score == 70.05
    assert rows[0].organization == "OpenAI"
    assert rows[0].metadata["tasks_passed_any"] == 98
    assert rows[1].organization == "Moonshot AI"


def test_parse_deepswe_without_reasoning_effort():
    html = '''[{model:"deepseek-v4-pro",harness:"mini-swe-agent",config:"default",source:"deep-swe",pass_rate:0.083,n_tasks_attempted:113,n_tasks_passed_any:9,mean_cost_usd:4.22},{model:"gpt-5-5",harness:"mini-swe-agent",reasoning_effort:"high",config:"default",source:"deep-swe",pass_rate:0.6195,n_tasks_attempted:113,n_tasks_passed_any:70,mean_cost_usd:4.47}]'''
    rows = parse_deepswe_html(html)
    assert len(rows) == 2
    assert rows[0].model == "gpt-5-5 [high]"
    assert rows[0].score == 61.95
    assert rows[1].model == "deepseek-v4-pro"
    assert rows[1].score == 8.3
    assert rows[1].metadata["reasoning_effort"] is None


def test_parse_terminal_leaderboard_table():
    html = """
    <table><thead><tr><th></th><th>Rank</th><th>Agent</th><th>Model</th><th>Date</th><th>Agent Org</th><th>Model Org</th><th>Accuracy</th></tr></thead>
    <tbody><tr><td></td><td>1</td><td>vix</td><td>Claude Opus 4.7</td><td>2026-05-15</td><td>vix</td><td>Anthropic</td><td>90.2 % ± 2.1</td></tr></tbody></table>
    """
    rows = parse_terminal_html(html)
    assert rows[0].rank == 1
    assert rows[0].model == "Claude Opus 4.7"
    assert rows[0].score == 90.2
    assert rows[0].metadata["agent"] == "vix"


def test_parse_benchlm_next_data_leaderboard():
    next_data = {
        "props": {"pageProps": {"leaderboard": [
            {"model": "GPT-5.5 Pro", "creator": "OpenAI", "sourceType": "Proprietary", "score": 90.1, "contextWindow": "1M"},
            {"model": "Kimi K2.6", "creator": "Moonshot AI", "sourceType": "Open", "score": 83.2, "contextWindow": "256K"},
        ]}}
    }
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>'
    rows = parse_benchlm_next_data(html)
    assert [r.rank for r in rows] == [1, 2]
    assert rows[1].model == "Kimi K2.6"
    assert rows[1].score == 83.2
    assert rows[1].metadata["source_type"] == "Open"


def test_parse_osworld_workbook_sorts_numeric_scores():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Eval Results"
    ws.append(["Model", "Institution", "PaperLink", "PaperAuthors", "Approach type", "Max steps", "Additional a11y tree used", "Additional coding-based action", "Multiple rollout", "Date", "Success rate", "Success/Total"])
    ws.append(["weak-agent", "Example", "", "", "General model", 15, "No", "No", "No", "2026-01-01", 12.3, "44/361"])
    ws.append(["strong-agent", "Example", "", "", "General model", 50, "No", "No", "No", "2026-01-02", 31.4, "113/360"])
    ws.append(["pending", "Example", "", "", "Unknown", None, "No", "No", "No", None, "🚧", None])
    buf = io.BytesIO()
    wb.save(buf)
    rows = parse_osworld_workbook(buf.getvalue())
    assert rows[0].model == "strong-agent"
    assert rows[0].score == 31.4
    assert rows[0].metadata["success_total"] == "113/360"
    assert len(rows) == 2


def test_parse_longbench_table_prefers_cot_overall_when_plain_missing():
    html = """
    <table><tr><th>#</th><th>Model</th><th>Params</th><th>Context</th><th>Date</th><th>Overall (%)</th><th>w/ CoT</th></tr>
    <tr><td></td><td>Gemini-2.5-Pro 🧠 Google</td><td>-</td><td>1M</td><td>2025-03-25</td><td>-</td><td>63.3</td></tr></table>
    """
    rows = parse_longbench_html(html)
    assert rows[0].model.startswith("Gemini-2.5-Pro")
    assert rows[0].organization == "Google"
    assert rows[0].score == 63.3
    assert rows[0].metadata["context"] == "1M"


def test_parse_longbench_html_skips_human_row():
    html = """
    <table><tr><th>#</th><th>Model</th><th>Params</th><th>Context</th><th>Date</th><th>Overall (%)</th><th>w/ CoT</th></tr>
    <tr><td>1</td><td>Gemini-2.5-Pro Google</td><td>-</td><td>1M</td><td>2025-03-25</td><td>63.3</td><td>-</td></tr>
    <tr><td>-</td><td>Human</td><td>-</td><td>-</td><td>-</td><td>53.7</td><td>-</td></tr>
    <tr><td>3</td><td>GPT-4o OpenAI</td><td>-</td><td>128K</td><td>2024-09-01</td><td>50.1</td><td>-</td></tr>
    </table>
    """
    rows = parse_longbench_html(html)
    assert len(rows) == 2
    assert all(r.model.lower() != "human" for r in rows)
    assert rows[0].score == 63.3


def test_parse_benchlm_next_data_custom_score_unit():
    next_data = {
        "props": {"pageProps": {"leaderboard": [
            {"model": "Claude Opus 4.8", "creator": "Anthropic", "score": 1890, "sourceType": "Proprietary"},
            {"model": "GPT-5.5", "creator": "OpenAI", "score": 1769, "sourceType": "Proprietary"},
        ]}}
    }
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>'
    rows = parse_benchlm_next_data(html, score_unit="Elo rating")
    assert rows[0].score_unit == "Elo rating"
    assert rows[0].model == "Claude Opus 4.8"
    assert rows[0].score == 1890.0


def test_parse_lmarena_rows_from_hf_dataset_response():
    payload = {"rows": [{"row": {"model_name": "claude-opus-4-6-thinking", "organization": "anthropic", "license": "Proprietary", "rating": 1499.3, "rating_lower": 1495.0, "rating_upper": 1503.5, "vote_count": 34186, "rank": 1, "category": "overall", "leaderboard_publish_date": "2026-05-27"}}]}
    rows = parse_lmarena_rows(payload)
    assert rows[0].model == "claude-opus-4-6-thinking"
    assert rows[0].organization == "Anthropic"
    assert rows[0].score == 1499.3
    assert rows[0].metadata["votes"] == 34186


# ── Retry logic ──────────────────────────────────────────────────────────────

def test_fetch_with_retry_succeeds_on_second_attempt():
    call_count = 0

    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("transient")
        return [BenchmarkRow(rank=1, model="X", organization=None, score=50.0, score_unit="% test")]

    with patch("benchmark_dashboard.sources.time") as mock_time:
        rows = _fetch_with_retry(flaky, delays=(0.001,))

    assert len(rows) == 1
    assert call_count == 2
    mock_time.sleep.assert_called_once_with(0.001)


def test_fetch_with_retry_exhausted_raises_last_exception():
    def always_fails():
        raise ValueError("always fails")

    with patch("benchmark_dashboard.sources.time"), pytest.raises(ValueError, match="always fails"):
        _fetch_with_retry(always_fails, delays=(0.001, 0.001))


def test_fetch_with_retry_no_retry_needed_on_first_success():
    with patch("benchmark_dashboard.sources.time") as mock_time:
        rows = _fetch_with_retry(
            lambda: [BenchmarkRow(rank=1, model="Y", organization=None, score=70.0, score_unit="% test")],
            delays=(0.001,),
        )
    assert len(rows) == 1
    mock_time.sleep.assert_not_called()


def test_fetch_with_retry_treats_empty_result_as_failure():
    call_count = 0

    def returns_empty_then_data():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return []
        return [BenchmarkRow(rank=1, model="Z", organization=None, score=60.0, score_unit="% test")]

    with patch("benchmark_dashboard.sources.time"):
        rows = _fetch_with_retry(returns_empty_then_data, delays=(0.001,))

    assert call_count == 2
    assert rows[0].model == "Z"


# ── _find_col ────────────────────────────────────────────────────────────────

def test_find_col_exact_match_takes_priority():
    headers = ["", "Agent Org", "Agent", "Model", "Accuracy"]
    assert _find_col(headers, "agent") == 2
    assert _find_col(headers, "agent org") == 1


def test_find_col_substring_fallback():
    headers = ["Score (Overall)", "Name"]
    assert _find_col(headers, "overall") == 0


def test_find_col_returns_none_when_absent():
    assert _find_col(["Rank", "Model", "Score"], "date") is None


# ── Semantic column detection ─────────────────────────────────────────────────

def test_parse_terminal_html_reordered_columns():
    html = """
    <table>
    <thead><tr><th>Agent</th><th>Rank</th><th>Model</th><th>Accuracy</th><th>Date</th><th>Model Org</th><th>Agent Org</th></tr></thead>
    <tbody><tr><td>myagent</td><td>1</td><td>Claude Opus 4.8</td><td>85.3 %</td><td>2026-05</td><td>Anthropic</td><td>myorg</td></tr></tbody>
    </table>
    """
    rows = parse_terminal_html(html)
    assert rows[0].rank == 1
    assert rows[0].model == "Claude Opus 4.8"
    assert rows[0].score == 85.3
    assert rows[0].metadata["agent"] == "myagent"
    assert rows[0].organization == "Anthropic"


def test_parse_longbench_html_reordered_columns():
    html = """
    <table>
    <tr><th>Date</th><th>Model</th><th>Overall (%)</th><th>Context</th><th>Params</th><th>w/ CoT</th></tr>
    <tr><td>2025-03</td><td>GPT-5.5 OpenAI</td><td>75.0</td><td>512K</td><td>-</td><td>-</td></tr>
    </table>
    """
    rows = parse_longbench_html(html)
    assert len(rows) == 1
    assert rows[0].score == 75.0
    assert rows[0].metadata["context"] == "512K"
    assert rows[0].organization == "OpenAI"


# ── Sanity validation ─────────────────────────────────────────────────────────

def _make_rows(n: int, score: float = 50.0) -> list[BenchmarkRow]:
    return [BenchmarkRow(rank=i + 1, model=f"M{i}", organization=None, score=score - i, score_unit="% test") for i in range(n)]


def test_validate_snapshot_warns_on_too_few_rows():
    warning = _validate_snapshot(_make_rows(2), min_rows=5, score_range=None)
    assert warning is not None
    assert "2" in warning


def test_validate_snapshot_warns_on_score_above_range():
    warning = _validate_snapshot(_make_rows(5, score=150.0), min_rows=5, score_range=(0.0, 100.0))
    assert warning is not None
    assert "150" in warning


def test_validate_snapshot_warns_on_score_below_range():
    warning = _validate_snapshot(_make_rows(5, score=-5.0), min_rows=5, score_range=(0.0, 100.0))
    assert warning is not None


def test_validate_snapshot_passes_for_valid_data():
    warning = _validate_snapshot(_make_rows(10, score=75.0), min_rows=5, score_range=(0.0, 100.0))
    assert warning is None


def test_validate_snapshot_no_range_check_when_none():
    warning = _validate_snapshot(_make_rows(10, score=9999.0), min_rows=5, score_range=None)
    assert warning is None
