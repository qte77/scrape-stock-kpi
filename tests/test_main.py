"""Tests for :mod:`src.__main__` helpers (pure-function layer only).

The Rich-table printing side is not unit-tested by convention
(``src/__main__.py`` is excluded from coverage in ``pyproject.toml``).
``_summary_row`` is a pure list-builder and is the smallest unit
worth pinning so the website / CLI column parity contract doesn't
silently drift.
"""

from __future__ import annotations

from src.__main__ import _summary_row
from src.composite_scores import CompositeScores
from src.fundamentals import FundamentalsSnapshot


def _snap(**kwargs: object) -> FundamentalsSnapshot:
    return FundamentalsSnapshot(symbol="X", **kwargs)  # type: ignore[arg-type]


def test_summary_row_matches_13_column_dashboard_order() -> None:
    """``_summary_row`` mirrors ``docs/demo/index.html`` column order.

    Inputs chosen so every field formats to a clean string.
    """
    snap = _snap(
        long_name="Test Co",
        sector="Technology",
        forward_pe=20.0,
        trailing_peg_ratio=1.5,
        beta=1.0,
        rd_to_revenue=0.10,
        operating_margins=0.20,
        return_on_equity=0.25,
        return_on_assets=0.10,
        current_ratio=2.0,
        sortino_ratio=1.5,
        composite_scores=CompositeScores(screener_score=72.4),
    )
    row = _summary_row(snap, show_scores=False)
    assert row == [
        "X",
        "Test Co",
        "Technology",
        "20.00",
        "1.50",
        "1.00",
        "10.00%",
        "20.00%",
        "25.00%",
        "10.00%",
        "2.00",
        "1.50",
        "72",
    ]


def test_summary_row_show_scores_appends_three_legacy_columns() -> None:
    """``--show-scores`` adds Quality / Dividend / Growth to the 13 base cols."""
    snap = _snap(
        composite_scores=CompositeScores(
            quality=80.0, dividend=60.0, growth=70.0, screener_score=72.5
        ),
    )
    base = _summary_row(snap, show_scores=False)
    extended = _summary_row(snap, show_scores=True)
    assert len(extended) == len(base) + 3
    assert extended[-3:] == ["80", "60", "70"]


def test_summary_row_sparse_snapshot_renders_dashes() -> None:
    """Sparse snapshot (FX / futures / crypto) renders dashes throughout."""
    row = _summary_row(_snap(), show_scores=False)
    assert row[0] == "X"
    # Every numeric column should be "-" when its input is missing.
    assert all(cell == "-" for cell in row[1:])
