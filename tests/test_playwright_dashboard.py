"""Browser-level acceptance tests for the rendered dashboard.

These tests serve the *actual committed artifact* (public/index.html) through the
real server module and drive a real Chromium browser via Playwright. They encode
two acceptance criteria from the maintainer:

1. The new "AA Intelligence Index" benchmark card must appear on the page with
   real rows (when its source fetch succeeded).
2. Nothing pre-existing may be removed — all original benchmark cards must
   still be present.

The tests skip cleanly when Playwright or a Chromium build is unavailable (e.g.
minimal CI machines), so the pure unit-test suite remains hermetic.
"""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api", reason="Playwright not installed")
from playwright.sync_api import sync_playwright  # noqa: E402

from benchmark_dashboard.server import DashboardHandler  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"

# Cards that existed before the AA Intelligence Index integration — the page
# must never lose any of them.
PRE_EXISTING_CARD_IDS = [
    "deep_swe",
    "gdpval_aa",
    "terminal_bench",
    "browsecomp",
    "osworld_verified",
    "longbench_v2",
    "lmarena_text_style",
    "hf_local_under10b",
    "hf_local_10to20b",
    "bigcodebench_under10b",
    "bigcodebench_10to20b",
]


@pytest.fixture(scope="module")
def base_url():
    """Serve public/ through the real DashboardHandler on an ephemeral port."""
    handler = partial(DashboardHandler, directory=str(PUBLIC_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as exc:  # noqa: BLE001
                pytest.skip(f"Chromium not launchable: {exc}")
            yield browser
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Playwright unavailable: {exc}")


@pytest.fixture(scope="module")
def dashboard_page(browser, base_url):
    page = browser.new_page(viewport={"width": 1280, "height": 1600})
    response = page.goto(base_url, wait_until="domcontentloaded", timeout=20000)
    assert response is not None and response.ok, f"dashboard did not load: {response and response.status}"
    yield page
    page.close()


def test_dashboard_serves_and_renders_title(dashboard_page):
    assert "LLM Agent Benchmark Dashboard" in dashboard_page.title()


def test_aa_intelligence_index_card_appears_with_content(dashboard_page):
    card = dashboard_page.locator("section#aa_intelligence_index")
    assert card.count() == 1, "AA Intelligence Index card is missing from the page"
    assert "AA Intelligence Index" in card.locator("h2").inner_text()
    # Provenance: source link back to Artificial Analysis must be visible.
    source_link = card.locator('a[href*="artificialanalysis.ai"]')
    assert source_link.count() >= 1, "card has no Artificial Analysis source link"
    # When the source fetch succeeded, the table must contain real model rows.
    embedded = json.loads(dashboard_page.locator("#benchmark-data").inner_text())
    snapshot = next(b for b in embedded["benchmarks"] if b["id"] == "aa_intelligence_index")
    if snapshot["status"] == "ok":
        rows = card.locator("tbody tr")
        assert rows.count() >= 10, f"expected ≥10 model rows, found {rows.count()}"
        first_model = rows.first.locator("td").nth(1).inner_text()
        assert first_model.strip(), "first row has no model name"
        score_text = rows.first.locator("td.score").inner_text()
        assert "index points" in score_text


def test_no_pre_existing_cards_were_removed(dashboard_page):
    for card_id in PRE_EXISTING_CARD_IDS:
        assert dashboard_page.locator(f"section#{card_id}").count() == 1, f"card #{card_id} was removed"


def test_embedded_snapshot_json_contains_aa_intelligence_index(dashboard_page):
    embedded = json.loads(dashboard_page.locator("#benchmark-data").inner_text())
    ids = [b["id"] for b in embedded["benchmarks"]]
    assert "aa_intelligence_index" in ids
    # All pre-existing snapshots must still be in the data too.
    for card_id in PRE_EXISTING_CARD_IDS:
        assert card_id in ids


def test_aa_intelligence_index_card_sits_between_deepswe_and_gdpval(dashboard_page):
    """Maintainer-requested position: DeepSWE → AA Intelligence Index → GDPval-AA."""
    card_ids = dashboard_page.locator("main section.benchmark-card").evaluate_all(
        "(els) => els.map((el) => el.id).filter(Boolean)"
    )
    assert card_ids.index("deep_swe") < card_ids.index("aa_intelligence_index") < card_ids.index("gdpval_aa"), (
        f"unexpected card order: {card_ids}"
    )
