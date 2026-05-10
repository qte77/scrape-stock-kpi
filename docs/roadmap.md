# Roadmap

Issues link to [GitHub Issues](https://github.com/qte77/scrape-stock-kpi/issues). See [`UserStory.md`](UserStory.md) for product intent and [`architecture.md`](architecture.md) for module structure.

## 0.3.0 — Tooling foundation [x]

Adopt qte77 ecosystem conventions (uv, ruff, pyright, Makefile, AGENTS.md, validate.yaml CI), Apache-2.0 license, working `make run`, runtime fixes.

**Shipped:** PR #2 (uv+ruff+pyright stack), #11 (plugins), #12 (orphan cleanup), #13 (pyright gate), #14 (Apache-2.0 + badges + `make run`), #15 (runtime fixes).

## 0.4.0 — Library-based KPI architecture [x]

Replace the Traderfox Playwright scraper with library-based fundamentals, asset-universe abstraction, and CNN F&G sentiment.

**Shipped:**

- [x] Governance scaffold + complexity gates wired into CI — PR #24
- [x] Decommission Traderfox scraper — issue [#19](https://github.com/qte77/scrape-stock-kpi/issues/19), PR #25
- [x] Universe layer (stocks/ETFs/FX/commodities/crypto/indices via Yahoo symbology) — issue [#20](https://github.com/qte77/scrape-stock-kpi/issues/20), PR #26
- [x] Mandatory markdownlint + lychee link checking (qte77 convention) — PRs #27 + #28
- [x] Fundamentals via yfinance — `FundamentalsSnapshot` with identity / valuation / profitability / financial health / growth / dividends / per-share / 52-week range fields. `financetoolkit` deferred per [ADR-0001](decisions/0001-defer-financetoolkit.md) — issue [#16](https://github.com/qte77/scrape-stock-kpi/issues/16), PR #28
- [x] CNN Fear & Greed sentiment + scheduled workflow — issue [#17](https://github.com/qte77/scrape-stock-kpi/issues/17), PRs #30-#37
- [x] README rewrite reflecting new architecture — issue [#3](https://github.com/qte77/scrape-stock-kpi/issues/3), PR #40

## 0.5.0 — Composite proxy scores [x]

Reproduce Traderfox-style aggregate signals as transparent, formula-documented composites built on v0.4.0's fundamentals. Simplified formulas use only point-in-time `FundamentalsSnapshot` inputs plus `info["beta"]`; multi-year trend formulas (Piotroski, CAGR, FCF coverage) are deliberately deferred per [ADR-0002](decisions/0002-simplified-composites.md).

**Shipped:**

- [x] `CompositeScores(BaseModel)` with quality / dividend / growth / big_call / aaqs / hgi proxies; each formula documented in docstrings — issue [#18](https://github.com/qte77/scrape-stock-kpi/issues/18), PR #42

## 0.5.1 — Data-quality follow-ups

Patch release covering issues surfaced by the v0.5.0 composites work.

**Goals:**

- [ ] Normalize `dividend_yield` at the ingest boundary so the table render, JSON output, and composite formulas all see one convention — issue [#43](https://github.com/qte77/scrape-stock-kpi/issues/43)

## 0.6.0+ — Deferred (revisit after composites ship)

- [ ] Long/short hedging strategy: relative-strength + regime-split + ranking — epic [#4](https://github.com/qte77/scrape-stock-kpi/issues/4) with sub-issues [#8](https://github.com/qte77/scrape-stock-kpi/issues/8), [#9](https://github.com/qte77/scrape-stock-kpi/issues/9), [#10](https://github.com/qte77/scrape-stock-kpi/issues/10)

## Open research (no milestone)

- [ ] TradingView screener evaluation — issue [#21](https://github.com/qte77/scrape-stock-kpi/issues/21)
- [ ] Alternative risk-sentiment sources (UBS, AAII, NAAIM, etc.) — issue [#22](https://github.com/qte77/scrape-stock-kpi/issues/22)
- [ ] pandas alternatives (Polars, Dask, Modin, etc.) — issue [#23](https://github.com/qte77/scrape-stock-kpi/issues/23)

## Out of scope

- CDS spreads (paid data only)
- Paid-API integrations (Tiingo, FMP premium, Alpha Vantage premium, Bloomberg)
- Trade execution (analysis only)
- Repo rename (defer; "scrape-stock-kpi" stays even after Traderfox removal — CNN F&G remains an HTTP fetch from a non-public-API endpoint)
