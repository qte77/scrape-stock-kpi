"""Fundamentals fetched from Yahoo Finance via yfinance.

Public API:
    - :func:`fetch_fundamentals` returns a :class:`FundamentalsSnapshot`
    - :func:`fetch_price_history` returns OHLCV as a pandas ``DataFrame``
    - :func:`fetch_universe_fundamentals` runs sequential fetches with a
      progress bar; per-ticker errors are logged and the ticker is skipped
      so the run does not crash on a single bad symbol.

All numeric snapshot fields are ``Optional[float]`` because yfinance
returns sparse ``info`` for non-equities (FX ``EURUSD=X``, futures
``GC=F``, crypto ``BTC-USD``). Sparse snapshots are valid by design.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import yfinance as yf
from pydantic import BaseModel, ConfigDict, Field
from tqdm import tqdm

from .composite_scores import CompositeScores

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class FundamentalsSnapshot(BaseModel):
    """Point-in-time fundamentals for a single Yahoo Finance ticker.

    Field aliases mirror yfinance ``info`` keys (camelCase) so a snapshot
    can be built with ``model_validate(yf.Ticker(t).info)``. Tests construct
    via snake_case kwargs because ``populate_by_name=True``.
    """

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    # -- identity --
    symbol: str
    long_name: str | None = Field(default=None, alias="longName")
    short_name: str | None = Field(default=None, alias="shortName")
    quote_type: str | None = Field(default=None, alias="quoteType")
    sector: str | None = None
    industry: str | None = None
    currency: str | None = None
    exchange: str | None = None

    # -- valuation --
    market_cap: float | None = Field(default=None, alias="marketCap")
    trailing_pe: float | None = Field(default=None, alias="trailingPE")
    forward_pe: float | None = Field(default=None, alias="forwardPE")
    price_to_book: float | None = Field(default=None, alias="priceToBook")
    price_to_sales_ttm: float | None = Field(
        default=None, alias="priceToSalesTrailing12Months"
    )
    enterprise_value: float | None = Field(default=None, alias="enterpriseValue")
    enterprise_to_ebitda: float | None = Field(default=None, alias="enterpriseToEbitda")

    # -- profitability --
    return_on_equity: float | None = Field(default=None, alias="returnOnEquity")
    return_on_assets: float | None = Field(default=None, alias="returnOnAssets")
    profit_margins: float | None = Field(default=None, alias="profitMargins")
    gross_margins: float | None = Field(default=None, alias="grossMargins")
    operating_margins: float | None = Field(default=None, alias="operatingMargins")

    # -- financial health --
    debt_to_equity: float | None = Field(default=None, alias="debtToEquity")
    current_ratio: float | None = Field(default=None, alias="currentRatio")
    quick_ratio: float | None = Field(default=None, alias="quickRatio")

    # -- growth --
    revenue_growth: float | None = Field(default=None, alias="revenueGrowth")
    earnings_growth: float | None = Field(default=None, alias="earningsGrowth")

    # -- dividends --
    dividend_yield: float | None = Field(default=None, alias="dividendYield")
    payout_ratio: float | None = Field(default=None, alias="payoutRatio")

    # -- per-share --
    trailing_eps: float | None = Field(default=None, alias="trailingEps")
    forward_eps: float | None = Field(default=None, alias="forwardEps")
    book_value: float | None = Field(default=None, alias="bookValue")

    # -- 52-week range --
    fifty_two_week_high: float | None = Field(default=None, alias="fiftyTwoWeekHigh")
    fifty_two_week_low: float | None = Field(default=None, alias="fiftyTwoWeekLow")

    # -- volatility --
    beta: float | None = None

    # -- enrichment (attached post-fetch via ``model_copy``) --
    composite_scores: CompositeScores | None = None


def fetch_fundamentals(ticker: str) -> FundamentalsSnapshot:
    """Fetch fundamentals for one ticker. Sparse for non-equities."""
    info: dict[str, Any] = yf.Ticker(ticker).info
    return FundamentalsSnapshot.model_validate({**info, "symbol": ticker})


def fetch_price_history(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Fetch OHLCV via ``yf.Ticker(ticker).history(period=period)``."""
    return yf.Ticker(ticker).history(period=period)


def fetch_universe_fundamentals(
    tickers: list[str], *, show_progress: bool = True
) -> list[FundamentalsSnapshot]:
    """Sequential fetch with tqdm. Per-ticker errors are logged and skipped."""
    iterable = tqdm(tickers, desc="fundamentals") if show_progress else tickers
    snapshots: list[FundamentalsSnapshot] = []
    for ticker in iterable:
        try:
            snapshots.append(fetch_fundamentals(ticker))
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", ticker, exc)
    return snapshots
