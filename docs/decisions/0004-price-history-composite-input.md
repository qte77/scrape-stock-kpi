# ADR-0004 — Allow price-history-derived inputs in composite scores

**Status:** Accepted (2026-05-14)

**Amends:** [ADR-0002](0002-simplified-composites.md) §Decision
("point-in-time inputs only")

**Drives:** PR `feature/kpi-dashboard-expansion` — adds the
`screener_score` 7th composite and the `sortino_ratio` snapshot field.

## Context

ADR-0002 scoped every composite to point-in-time inputs from
`Ticker.info` (plus the cheap addition of `info["beta"]`). Sortino,
the canonical retail risk-adjusted-return metric, requires the
distribution of daily returns and therefore a price-history series —
data ADR-0002 explicitly left for a future ADR.

Pulling per-ticker price history at composite time would multiply
HTTP traffic on every `make run`. yfinance's batched call,
`yf.download(tickers, period="1y")`, returns close prices for the
whole universe in one roundtrip — making the Sortino input cheap
enough to justify extending the composite-input scope.

## Decision

Composite-score functions may read price-history-derived snapshot
fields in addition to `Ticker.info` point-in-time fields. As of this
ADR the only such field is `sortino_ratio`, attached to
`FundamentalsSnapshot` post-fetch via `model_copy`.

`fetch_universe_fundamentals` gains a single batched
`yf.download(tickers, period="1y", progress=False, auto_adjust=True)`
before the per-ticker loop. Failure of the batch call leaves every
`sortino_ratio` as `None` — the rest of the universe fetch is
unaffected. This is the first batched yfinance call in the
codebase; the existing per-ticker `Ticker.info` / `Ticker.history` /
`Ticker.income_stmt` pattern stays.

## Consequences

- `screener_score(snap)` consumes `snap.sortino_ratio` alongside the
  other 8 visible-column inputs; missing terms still drop out per
  the existing mean-of-present-terms convention.
- Sparse-snapshot rule is preserved: ETFs / FX / futures / crypto
  with insufficient price history (< 30 datapoints in 1y) get
  `sortino_ratio = None` and the term drops from the Score.
- One extra HTTP roundtrip per `make run`, independent of universe
  size. Negligible rate-limit risk.
- International coverage stays full: yfinance price history is
  global.

## Out-of-scope

- Multi-year fundamentals (Piotroski, ROIC stability, 5y CAGR, FCF
  coverage) — still deferred per ADR-0001 / ADR-0002.
- Other price-history-derived composites (Mansfield RS,
  beta-adjusted excess return) — deferred per ADR-0003.
- Replacing the existing per-ticker `Ticker.history` boundary used
  by `fetch_price_history` for ad-hoc one-ticker calls.
