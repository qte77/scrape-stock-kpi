"""Composite proxy scores derived from a `FundamentalsSnapshot`.

Six 0-100 proxies inspired by the Traderfox aggregate scores referenced
in issue #18. Formulas are intentionally simplified: each composite uses
only the point-in-time fields already carried on `FundamentalsSnapshot`
plus ``beta`` from yfinance info. Multi-year trend formulas (Piotroski,
ROIC stability, 5y CAGR, FCF coverage) are deliberately deferred — see
``docs/decisions/0002-simplified-composites.md``.

Public API:
    - :class:`CompositeScores` — frozen pydantic model holding the six
      proxy scores.
    - :func:`compute_scores` — entry point that takes a
      `FundamentalsSnapshot` and returns a fully-populated
      :class:`CompositeScores`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .fundamentals import FundamentalsSnapshot


_ROE_LO, _ROE_HI = 0.0, 0.30
_ROA_LO, _ROA_HI = 0.0, 0.15
_OP_MARGIN_LO, _OP_MARGIN_HI = 0.0, 0.30
_DE_LO, _DE_HI = 0.0, 200.0
_YIELD_LO, _YIELD_HI = 0.0, 0.07
_GROWTH_LO, _GROWTH_HI = -0.20, 0.50
_BETA_LO, _BETA_HI = 0.0, 2.0

_FORWARD_PE_LO, _FORWARD_PE_HI = 5.0, 40.0
_PEG_LO, _PEG_HI = 0.0, 3.0
_RD_REV_LO, _RD_REV_HI = 0.0, 0.20
_CURRENT_LO, _CURRENT_HI = 1.0, 3.0
_SORTINO_LO, _SORTINO_HI = 0.0, 3.0
_SCREENER_MIN_TERMS = 5

_HGI_MARGIN_THRESHOLD = 0.10
_HGI_MARGIN_BONUS = 10.0


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _rescale(value: float, lo: float, hi: float) -> float:
    """Linear rescale of ``value`` clamped to ``[lo, hi]`` into ``[0, 100]``."""
    return (_clamp(value, lo, hi) - lo) / (hi - lo) * 100


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


class CompositeScores(BaseModel):
    """Seven 0-100 proxy scores derived from a single `FundamentalsSnapshot`.

    Any score is ``None`` when its required inputs were unavailable.
    ``big_call`` reweights proportionally over its non-``None`` components
    so a tech stock with no dividend still receives a robustness score.
    ``screener_score`` aggregates the visible main-table KPIs (see
    `docs/decisions/0004-price-history-composite-input.md`).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    quality: float | None = None
    dividend: float | None = None
    growth: float | None = None
    big_call: float | None = None
    aaqs: float | None = None
    hgi: float | None = None
    screener_score: float | None = None


def quality(snap: FundamentalsSnapshot) -> float | None:
    """Average of normalized ROE, ROA, operating margin, inverted D/E.

    Negative D/E (negative shareholder equity) drops the leverage term;
    the score is averaged over the remaining three. Returns ``None`` when
    all four inputs are unavailable.
    """
    terms: list[float] = []
    if snap.return_on_equity is not None:
        terms.append(_rescale(snap.return_on_equity, _ROE_LO, _ROE_HI))
    if snap.return_on_assets is not None:
        terms.append(_rescale(snap.return_on_assets, _ROA_LO, _ROA_HI))
    if snap.operating_margins is not None:
        terms.append(
            _rescale(snap.operating_margins, _OP_MARGIN_LO, _OP_MARGIN_HI)
        )
    if snap.debt_to_equity is not None and snap.debt_to_equity >= 0:
        terms.append(100 - _rescale(snap.debt_to_equity, _DE_LO, _DE_HI))
    return _mean(terms) if terms else None


def dividend(snap: FundamentalsSnapshot) -> float | None:
    """Yield + payout-ratio sweet spot. Tilts toward ~50% payout.

    Returns ``None`` when both yield and payout ratio are unavailable.
    """
    terms: list[float] = []
    if snap.dividend_yield is not None:
        terms.append(_rescale(snap.dividend_yield, _YIELD_LO, _YIELD_HI))
    if snap.payout_ratio is not None:
        sweet_spot = max(0.0, 1 - 2 * abs(snap.payout_ratio - 0.5))
        terms.append(sweet_spot * 100)
    return _mean(terms) if terms else None


def growth(snap: FundamentalsSnapshot) -> float | None:
    """Average of point-in-time revenue growth + earnings growth.

    Each component clamped to ``[_GROWTH_LO, _GROWTH_HI]`` and rescaled
    linearly. Returns ``None`` when both growth fields are unavailable.
    """
    terms: list[float] = []
    if snap.revenue_growth is not None:
        terms.append(_rescale(snap.revenue_growth, _GROWTH_LO, _GROWTH_HI))
    if snap.earnings_growth is not None:
        terms.append(_rescale(snap.earnings_growth, _GROWTH_LO, _GROWTH_HI))
    return _mean(terms) if terms else None


def big_call(
    quality_score: float | None,
    dividend_score: float | None,
    growth_score: float | None,
) -> float | None:
    """Weighted Quality/Dividend/Growth with proportional reweighting.

    Default weights 0.4 / 0.3 / 0.3. Missing components are dropped and
    the remaining weights renormalize. Returns ``None`` only when all
    three inputs are ``None``.
    """
    pairs: list[tuple[float, float]] = []
    if quality_score is not None:
        pairs.append((quality_score, 0.4))
    if dividend_score is not None:
        pairs.append((dividend_score, 0.3))
    if growth_score is not None:
        pairs.append((growth_score, 0.3))
    if not pairs:
        return None
    total_weight = sum(w for (_, w) in pairs)
    return sum(s * w for (s, w) in pairs) / total_weight


def aaqs(quality_score: float | None, beta: float | None) -> float | None:
    """Quality combined with low-volatility (low beta is better).

    Returns ``None`` when either input is unavailable — without beta this
    composite would degenerate to ``quality_score`` alone, which is
    already its own score.
    """
    if quality_score is None or beta is None:
        return None
    low_vol = _rescale(_BETA_HI - beta, _BETA_LO, _BETA_HI)
    return _mean([quality_score, low_vol])


def hgi(snap: FundamentalsSnapshot) -> float | None:
    """Growth-tilted approximation of Traderfox's GMG screen.

    Average of normalized revenue + earnings growth plus a fixed bonus
    when operating margin clears ``_HGI_MARGIN_THRESHOLD``. Returns
    ``None`` when both growth components are unavailable.
    """
    terms: list[float] = []
    if snap.revenue_growth is not None:
        terms.append(_rescale(snap.revenue_growth, _GROWTH_LO, _GROWTH_HI))
    if snap.earnings_growth is not None:
        terms.append(_rescale(snap.earnings_growth, _GROWTH_LO, _GROWTH_HI))
    if not terms:
        return None
    score = _mean(terms)
    if (
        snap.operating_margins is not None
        and snap.operating_margins > _HGI_MARGIN_THRESHOLD
    ):
        score = min(100.0, score + _HGI_MARGIN_BONUS)
    return score


def _normalize_term(
    value: float | None, lo: float, hi: float, *, invert: bool = False
) -> float | None:
    """Rescale ``value`` to ``[0, 100]`` clamped to ``[lo, hi]``.

    Returns ``None`` when ``value`` is ``None``. When ``invert=True``
    returns ``100 - rescaled`` so low input values produce high scores
    (used for cheapness / risk metrics where lower is better).
    """
    if value is None:
        return None
    raw = _rescale(value, lo, hi)
    return 100 - raw if invert else raw


def screener_score(snap: FundamentalsSnapshot) -> float | None:
    """Aggregated 0-100 composite of the 9 visible main-table KPIs.

    Reads from the snapshot itself (including the post-fetch enrichments
    ``rd_to_revenue`` and ``sortino_ratio``). ROI, Quick, Gross M, Net M
    and the Trail/Fwd ratio are deliberately NOT included — those are
    detail-panel KPIs and should not influence the at-a-glance ranking.

    Negative ``forward_pe`` (loss-making companies) drops the term
    rather than rewarding it via the inverted cheapness rescale.

    Returns ``None`` when fewer than ``_SCREENER_MIN_TERMS`` (5) of the
    9 KPIs are present — averaging a smaller subset would produce a
    score driven by which terms happened to be available rather than
    by the underlying signal.
    """
    forward_pe = (
        snap.forward_pe
        if snap.forward_pe is None or snap.forward_pe > 0
        else None
    )
    terms_inputs = (
        (forward_pe, _FORWARD_PE_LO, _FORWARD_PE_HI, True),
        (snap.trailing_peg_ratio, _PEG_LO, _PEG_HI, True),
        (snap.beta, _BETA_LO, _BETA_HI, True),
        (snap.rd_to_revenue, _RD_REV_LO, _RD_REV_HI, False),
        (snap.operating_margins, _OP_MARGIN_LO, _OP_MARGIN_HI, False),
        (snap.return_on_equity, _ROE_LO, _ROE_HI, False),
        (snap.return_on_assets, _ROA_LO, _ROA_HI, False),
        (snap.current_ratio, _CURRENT_LO, _CURRENT_HI, False),
        (snap.sortino_ratio, _SORTINO_LO, _SORTINO_HI, False),
    )
    terms: list[float] = []
    for value, lo, hi, invert in terms_inputs:
        norm = _normalize_term(value, lo, hi, invert=invert)
        if norm is not None:
            terms.append(norm)
    return _mean(terms) if len(terms) >= _SCREENER_MIN_TERMS else None


def compute_scores(snap: FundamentalsSnapshot) -> CompositeScores:
    """Compute every composite for a single snapshot."""
    q = quality(snap)
    d = dividend(snap)
    g = growth(snap)
    return CompositeScores(
        quality=q,
        dividend=d,
        growth=g,
        big_call=big_call(q, d, g),
        aaqs=aaqs(q, snap.beta),
        hgi=hgi(snap),
        screener_score=screener_score(snap),
    )
