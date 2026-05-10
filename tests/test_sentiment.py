"""Tests for :mod:`app.sentiment`."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
from app.sentiment import (
    ACCEPT,
    REFERER,
    USER_AGENT,
    FearGreedSnapshot,
    fetch_fear_greed,
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
    snap = FearGreedSnapshot(
        score=50.0,
        rating="neutral",
        timestamp=datetime.fromisoformat("2026-05-09T20:00:00+00:00"),
    )
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


@pytest.mark.network
def test_live_fetch_fear_greed() -> None:
    snap = fetch_fear_greed()
    assert 0.0 <= snap.score <= 100.0
    assert snap.rating
