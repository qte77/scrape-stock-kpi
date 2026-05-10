"""Tests for :mod:`app.sentiment`."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from app.sentiment import (
    ACCEPT,
    REFERER,
    USER_AGENT,
    FearGreedSnapshot,
    _load_year,
    _upsert,
    _write_year,
    fetch_fear_greed,
    merge_payload_into_years,
    parse_historical,
)
from pydantic import ValidationError

from tests.conftest import load_fear_greed_fixture


class _FakeResponse:
    """Minimal context-manager double for ``urllib.request.urlopen``."""

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_: object) -> bool:
        return False


def _snap(date_str: str, *, score: float = 50.0, rating: str = "neutral") -> FearGreedSnapshot:
    return FearGreedSnapshot(
        score=score,
        rating=rating,
        timestamp=datetime.fromisoformat(f"{date_str}T20:00:00+00:00"),
    )


def test_snapshot_parses_fixture_payload() -> None:
    payload = load_fear_greed_fixture("current")
    snap = FearGreedSnapshot.model_validate(payload["fear_and_greed"])
    assert snap.score == 56.42
    assert snap.rating == "neutral"
    assert snap.timestamp == datetime.fromisoformat("2026-05-09T20:00:00+00:00")
    assert snap.previous_close == 55.10
    assert snap.previous_1_week == 60.30
    assert snap.previous_1_month == 45.20
    assert snap.previous_1_year == 72.40


def test_snapshot_extra_keys_ignored() -> None:
    snap = FearGreedSnapshot.model_validate(
        {
            "score": 10.0,
            "rating": "extreme fear",
            "timestamp": "2026-05-09T20:00:00+00:00",
            "junk": "x",
            "another_unknown": 42,
        }
    )
    assert snap.score == 10.0
    assert snap.rating == "extreme fear"


def test_snapshot_is_frozen() -> None:
    snap = _snap("2026-05-09")
    with pytest.raises(ValidationError):
        snap.score = 99.0  # type: ignore[misc]


def test_fetch_fear_greed_returns_snapshot_from_payload() -> None:
    payload = load_fear_greed_fixture("current")

    with patch("app.sentiment.urllib.request.urlopen", return_value=_FakeResponse(payload)):
        snap = fetch_fear_greed()

    assert snap.score == 56.42
    assert snap.rating == "neutral"


def test_fetch_fear_greed_sends_browser_headers() -> None:
    payload = load_fear_greed_fixture("current")
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, **_: Any) -> _FakeResponse:
        captured["request"] = request
        return _FakeResponse(payload)

    with patch("app.sentiment.urllib.request.urlopen", side_effect=fake_urlopen):
        fetch_fear_greed()

    assert captured["request"].get_header("User-agent") == USER_AGENT
    assert captured["request"].get_header("Accept") == ACCEPT
    assert captured["request"].get_header("Referer") == REFERER
    # Guard against the regression that triggered the first hot-fix: CNN's
    # WAF rejects any UA containing the bot-style "(compatible;"
    # parenthetical.
    assert "(compatible;" not in USER_AGENT


def test_parse_historical_dedups_same_day_keeps_latest() -> None:
    payload = load_fear_greed_fixture("current")
    by_date = parse_historical(payload)

    # Fixture has 4 entries spanning 3 dates (two share 2025-05-05);
    # the later same-day entry (score=60.5) must win.
    assert set(by_date) == {"2025-05-05", "2025-05-06", "2025-05-07"}
    assert by_date["2025-05-05"].score == 60.5
    assert by_date["2025-05-05"].rating == "greed"
    assert by_date["2025-05-06"].score == 58.2
    assert by_date["2025-05-07"].rating == "neutral"
    # Historical points carry no `previous_*` data — they default to None.
    assert all(snap.previous_close is None for snap in by_date.values())


def test_parse_historical_handles_empty() -> None:
    assert parse_historical({}) == {}
    assert parse_historical({"fear_and_greed_historical": {"data": []}}) == {}


def test_upsert_force_always_wins() -> None:
    bucket: dict[str, FearGreedSnapshot] = {"2026-05-09": _snap("2026-05-09", score=10.0)}
    incoming = FearGreedSnapshot(
        score=99.0,
        rating="greed",
        timestamp=datetime.fromisoformat("2026-05-09T19:00:00+00:00"),
    )

    changed = _upsert(bucket, incoming, force=True)

    assert changed is True
    assert bucket["2026-05-09"].score == 99.0


def test_upsert_gapfill_skips_when_existing_is_newer() -> None:
    bucket: dict[str, FearGreedSnapshot] = {"2026-05-09": _snap("2026-05-09", score=10.0)}
    older = FearGreedSnapshot(
        score=99.0,
        rating="greed",
        timestamp=datetime.fromisoformat("2026-05-09T19:00:00+00:00"),
    )

    changed = _upsert(bucket, older, force=False)

    assert changed is False
    assert bucket["2026-05-09"].score == 10.0


def test_upsert_gapfill_inserts_when_missing() -> None:
    bucket: dict[str, FearGreedSnapshot] = {}
    snap = _snap("2026-05-09")

    changed = _upsert(bucket, snap, force=False)

    assert changed is True
    assert bucket["2026-05-09"] is snap


def test_write_then_load_year_roundtrip(tmp_path: Path) -> None:
    by_date = {
        "2026-01-15": _snap("2026-01-15", score=30.0, rating="fear"),
        "2026-03-02": _snap("2026-03-02", score=70.0, rating="greed"),
    }
    _write_year(2026, by_date, root=tmp_path)
    reloaded = _load_year(2026, root=tmp_path)

    assert set(reloaded) == set(by_date)
    assert reloaded["2026-01-15"].score == 30.0
    assert reloaded["2026-03-02"].rating == "greed"


def test_write_year_sorts_entries_by_date(tmp_path: Path) -> None:
    by_date = {
        "2026-03-02": _snap("2026-03-02"),
        "2026-01-15": _snap("2026-01-15"),
        "2026-02-20": _snap("2026-02-20"),
    }
    path = _write_year(2026, by_date, root=tmp_path)
    raw = json.loads(path.read_text())

    assert [item["timestamp"][:10] for item in raw] == [
        "2026-01-15",
        "2026-02-20",
        "2026-03-02",
    ]


def test_load_year_returns_empty_when_file_missing(tmp_path: Path) -> None:
    assert _load_year(2099, root=tmp_path) == {}


def test_merge_payload_into_years_groups_and_forces_today(tmp_path: Path) -> None:
    payload = load_fear_greed_fixture("current")
    by_year = merge_payload_into_years(payload, root=tmp_path)

    # Headline is dated 2026-05-09; historical spans 2025-05-{05,06,07}.
    assert set(by_year) == {2025, 2026}
    assert set(by_year[2025]) == {"2025-05-05", "2025-05-06", "2025-05-07"}
    assert "2026-05-09" in by_year[2026]
    today = by_year[2026]["2026-05-09"]
    assert today.previous_close == 55.10
    assert by_year[2025]["2025-05-05"].previous_close is None


def test_merge_payload_preserves_existing_dates_outside_history(tmp_path: Path) -> None:
    """Year files CNN no longer ships are untouched (main() never writes them)."""
    long_ago = _snap("2024-01-15", score=12.34, rating="extreme fear")
    _write_year(2024, {"2024-01-15": long_ago}, root=tmp_path)

    payload = load_fear_greed_fixture("current")
    by_year = merge_payload_into_years(payload, root=tmp_path)

    # 2024 is not in the returned mapping (no upsert touched it),
    # and the on-disk file is unchanged.
    assert 2024 not in by_year
    assert _load_year(2024, root=tmp_path)["2024-01-15"].score == 12.34


def test_merge_payload_does_not_clobber_today_with_stale_historical(
    tmp_path: Path,
) -> None:
    """If CNN's historical block also lists today, the live headline wins."""
    payload = load_fear_greed_fixture("current")
    today_iso = payload["fear_and_greed"]["timestamp"]
    today_dt = datetime.fromisoformat(today_iso).astimezone(UTC)
    payload["fear_and_greed_historical"]["data"].append(
        {"x": int(today_dt.timestamp() * 1000) - 60_000, "y": 1.0, "rating": "extreme fear"}
    )

    by_year = merge_payload_into_years(payload, root=tmp_path)

    today_key = today_dt.strftime("%Y-%m-%d")
    today = by_year[2026][today_key]
    assert today.score == 56.42
    assert today.rating == "neutral"
    assert today.previous_close == 55.10
    assert today_dt - today.timestamp == timedelta(0)


@pytest.mark.network
def test_live_fetch_fear_greed() -> None:
    snap = fetch_fear_greed()
    assert 0.0 <= snap.score <= 100.0
    assert snap.rating
