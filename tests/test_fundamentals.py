"""Tests for :mod:`src.fundamentals`."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError
from src.fundamentals import (
    FundamentalsSnapshot,
    fetch_fundamentals,
    fetch_price_history,
    fetch_universe_fundamentals,
)

from tests.conftest import load_fundamentals_fixture


def test_snapshot_parses_full_info_dict() -> None:
    info = load_fundamentals_fixture("AAPL")
    snap = FundamentalsSnapshot.model_validate(info)
    assert snap.symbol == "AAPL"
    assert snap.long_name == "Apple Inc."
    assert snap.sector == "Technology"
    assert snap.quote_type == "EQUITY"
    assert snap.market_cap is not None and snap.market_cap > 0
    assert snap.trailing_pe == 32.5
    assert snap.return_on_equity == 1.45
    assert snap.dividend_yield == 0.0048
    assert snap.beta == 1.24


def test_snapshot_beta_defaults_to_none_when_missing() -> None:
    snap = FundamentalsSnapshot.model_validate({"symbol": "X"})
    assert snap.beta is None


def test_snapshot_handles_sparse_info() -> None:
    info = load_fundamentals_fixture("GC=F")
    snap = FundamentalsSnapshot.model_validate(info)
    assert snap.symbol == "GC=F"
    assert snap.quote_type == "FUTURE"
    assert snap.currency == "USD"
    assert snap.market_cap is None
    assert snap.trailing_pe is None
    assert snap.return_on_equity is None
    assert snap.dividend_yield is None


def test_snapshot_extra_keys_ignored() -> None:
    info = {
        "symbol": "TEST",
        "longName": "Test Co",
        "junkKey1": "x",
        "another_junk": 42,
    }
    snap = FundamentalsSnapshot.model_validate(info)
    assert snap.symbol == "TEST"
    assert snap.long_name == "Test Co"


def test_snapshot_is_frozen() -> None:
    snap = FundamentalsSnapshot(symbol="X")
    with pytest.raises(ValidationError):
        snap.symbol = "Y"  # type: ignore[misc]


def test_fetch_universe_continues_on_error(caplog: pytest.LogCaptureFixture) -> None:
    aapl_info = load_fundamentals_fixture("AAPL")
    gold_info = load_fundamentals_fixture("GC=F")

    class _FakeTicker:
        def __init__(self, info: dict) -> None:
            self.info = info

    def fake_ticker(symbol: str) -> _FakeTicker:
        if symbol == "BROKEN":
            raise RuntimeError("simulated yfinance failure")
        return _FakeTicker(aapl_info if symbol == "AAPL" else gold_info)

    with (
        caplog.at_level("WARNING", logger="src.fundamentals"),
        patch("src.fundamentals.yf.Ticker", side_effect=fake_ticker),
    ):
        results = fetch_universe_fundamentals(
            ["AAPL", "BROKEN", "GC=F"], show_progress=False
        )

    assert len(results) == 2
    assert {s.symbol for s in results} == {"AAPL", "GC=F"}
    assert any("BROKEN" in rec.message for rec in caplog.records)


@pytest.mark.network
def test_live_fetch_aapl() -> None:
    snap = fetch_fundamentals("AAPL")
    assert snap.symbol == "AAPL"
    assert snap.market_cap is not None and snap.market_cap > 0
    assert snap.sector is not None


@pytest.mark.network
def test_live_fetch_history_returns_dataframe() -> None:
    df = fetch_price_history("AAPL", period="1mo")
    assert not df.empty
    assert "Close" in df.columns
