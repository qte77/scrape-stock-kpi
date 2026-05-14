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


def test_snapshot_parses_trailing_peg_ratio() -> None:
    """Trailing PEG ratio populates via the yfinance ``trailingPegRatio`` alias.

    yfinance ships ``info["pegRatio"]`` broken since June 2025 (issue #2570);
    ``trailingPegRatio`` continues to work and is fetched from a separate
    fundamentals-timeseries endpoint. We model only the working one.
    """
    snap = FundamentalsSnapshot.model_validate(
        {"symbol": "X", "trailingPegRatio": 1.23}
    )
    assert snap.trailing_peg_ratio == 1.23


def test_normalize_yfinance_info_divides_dividend_yield() -> None:
    """Recent yfinance ships dividendYield as a percentage value (e.g.
    0.37 for AAPL's 0.37 %). `_normalize_yfinance_info` divides by 100 at
    the fetch boundary so the rest of the codebase sees a fraction.
    """
    from src.fundamentals import _normalize_yfinance_info

    normalized = _normalize_yfinance_info({"dividendYield": 0.37, "trailingPE": 35.0})
    assert normalized["dividendYield"] == 0.0037
    assert normalized["trailingPE"] == 35.0  # untouched


def test_normalize_yfinance_info_handles_missing_yield() -> None:
    """Sparse snapshots (FX, futures, crypto) have no `dividendYield` key.
    The normalizer leaves the input dict structurally unchanged.
    """
    from src.fundamentals import _normalize_yfinance_info

    assert _normalize_yfinance_info({"symbol": "X"}) == {"symbol": "X"}


def test_fetch_fundamentals_normalizes_live_yield() -> None:
    """End-to-end: a mocked yf.Ticker.info shipping percentage-shaped
    dividendYield (current schema) reaches `fetch_fundamentals` and
    emerges with a fractional value on the snapshot.
    """
    from unittest.mock import patch

    class _FakeTicker:
        info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "dividendYield": 0.37,  # current yfinance: percentage-shaped
        }

    with patch("src.fundamentals.yf.Ticker", return_value=_FakeTicker()):
        snap = fetch_fundamentals("AAPL")
    assert snap.dividend_yield == 0.0037


def test_compute_roi_full_inputs() -> None:
    """ROI computed from five raw ``info`` keys.

    Inputs chosen so the arithmetic is exact:
    book_equity = marketCap / priceToBook = 1000 / 10 = 100
    invested_capital = book_equity + totalDebt - totalCash = 100 + 50 - 30 = 120
    roi = netIncomeToCommon / invested_capital = 24 / 120 = 0.20
    """
    from src.fundamentals import _compute_roi

    info = {
        "netIncomeToCommon": 24.0,
        "marketCap": 1000.0,
        "priceToBook": 10.0,
        "totalDebt": 50.0,
        "totalCash": 30.0,
    }
    assert _compute_roi(info) == 0.20


def test_compute_roi_missing_input_returns_none() -> None:
    """A single missing input collapses ROI to ``None``."""
    from src.fundamentals import _compute_roi

    info = {
        "netIncomeToCommon": 24.0,
        "marketCap": 1000.0,
        # priceToBook missing — ROI is not computable
        "totalDebt": 50.0,
        "totalCash": 30.0,
    }
    assert _compute_roi(info) is None


def test_compute_roi_zero_price_to_book_returns_none() -> None:
    """Avoid ``ZeroDivisionError`` when book equity cannot be derived."""
    from src.fundamentals import _compute_roi

    info = {
        "netIncomeToCommon": 24.0,
        "marketCap": 1000.0,
        "priceToBook": 0.0,
        "totalDebt": 50.0,
        "totalCash": 30.0,
    }
    assert _compute_roi(info) is None


def test_compute_roi_zero_invested_capital_returns_none() -> None:
    """``book_equity + totalDebt - totalCash == 0`` -> ``None``.

    Inputs: book_equity = 100, debt = 0, cash = 100 -> invested_capital = 0.
    """
    from src.fundamentals import _compute_roi

    info = {
        "netIncomeToCommon": 24.0,
        "marketCap": 1000.0,
        "priceToBook": 10.0,
        "totalDebt": 0.0,
        "totalCash": 100.0,
    }
    assert _compute_roi(info) is None


def test_snapshot_roi_defaults_to_none() -> None:
    """``roi`` field defaults to ``None`` on direct snapshot construction."""
    snap = FundamentalsSnapshot.model_validate({"symbol": "X"})
    assert snap.roi is None


def test_fetch_fundamentals_attaches_roi() -> None:
    """End-to-end: a mocked yfinance ``info`` dict with the five ROI
    inputs reaches the snapshot's ``roi`` field via ``model_copy``."""

    class _FakeTicker:
        info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "netIncomeToCommon": 24.0,
            "marketCap": 1000.0,
            "priceToBook": 10.0,
            "totalDebt": 50.0,
            "totalCash": 30.0,
        }

    with patch("src.fundamentals.yf.Ticker", return_value=_FakeTicker()):
        snap = fetch_fundamentals("AAPL")
    assert snap.roi == 0.20


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
