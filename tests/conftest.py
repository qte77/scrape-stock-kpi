"""Shared pytest fixtures for scrape-stock-kpi.

Tests follow Arrange / Act / Assert structure. Mark hardware-dependent or
network-dependent tests with the corresponding pytest markers (see pyproject.toml).
"""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fundamentals"


def load_fundamentals_fixture(symbol: str) -> dict:
    """Read a vendored yfinance ``info`` dict from ``tests/fixtures/fundamentals/``."""
    return json.loads((FIXTURES_DIR / f"{symbol}.json").read_text())
