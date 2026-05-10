"""Tests for :mod:`app.sentiment`."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
from app.sentiment import (
    USER_AGENT,
    FearGreedSnapshot,
    fetch_fear_greed,
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
        score=50.0, rating="neutral", timestamp=datetime.fromisoformat("2026-05-09T20:00:00+00:00")
    )
    with pytest.raises(ValidationError):
        snap.score = 99.0  # type: ignore[misc]


def test_fetch_fear_greed_returns_snapshot_from_payload() -> None:
    payload = load_fear_greed_fixture("current")

    with patch("app.sentiment.urllib.request.urlopen", return_value=_FakeResponse(payload)):
        snap = fetch_fear_greed()

    assert snap.score == 56.42
    assert snap.rating == "neutral"


def test_fetch_fear_greed_sends_user_agent_header() -> None:
    payload = load_fear_greed_fixture("current")
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, **_: Any) -> _FakeResponse:
        captured["request"] = request
        return _FakeResponse(payload)

    with patch("app.sentiment.urllib.request.urlopen", side_effect=fake_urlopen):
        fetch_fear_greed()

    assert captured["request"].get_header("User-agent") == USER_AGENT


@pytest.mark.network
def test_live_fetch_fear_greed() -> None:
    snap = fetch_fear_greed()
    assert 0.0 <= snap.score <= 100.0
    assert snap.rating
