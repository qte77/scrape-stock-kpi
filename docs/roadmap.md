# Roadmap

Issues link to [GitHub Issues](https://github.com/qte77/scrape-stock-kpi/issues). See [`UserStory.md`](UserStory.md) for product intent and [`architecture.md`](architecture.md) for module structure.

## 0.3.0 — Tooling foundation ✅

Adopt qte77 ecosystem conventions (uv, ruff, pyright, Makefile, AGENTS.md, validate.yaml CI), Apache-2.0 license, working `make run`, runtime fixes.

**Shipped:** PR #2 (uv+ruff+pyright stack), #11 (plugins), #12 (orphan cleanup), #13 (pyright gate), #14 (Apache-2.0 + badges + `make run`), #15 (runtime fixes).

## 0.4.0 — Library-based KPI architecture (in progress)

Replace the Traderfox Playwright scraper with library-based fundamentals, asset-universe abstraction, and CNN F&G sentiment.

**Goals:**

- Governance scaffold: architecture.md, UserStory.md, roadmap.md, ADRs; complexity gates wired into CI (this PR)
- Decommission Traderfox scraper — issue [#19](https://github.com/qte77/scrape-stock-kpi/issues/19)
- Universe layer (stocks/ETFs/FX/commodities/crypto/indices via Yahoo symbology) — issue [#20](https://github.com/qte77/scrape-stock-kpi/issues/20)
- Fundamentals via yfinance + financetoolkit (Piotroski, ROE/ROA/ROIC, Beta, PEG, margin, E/P, yield, Dividend Aristocrat flag) — issue [#16](https://github.com/qte77/scrape-stock-kpi/issues/16)
- CNN Fear & Greed sentiment + scheduled workflow — issue [#17](https://github.com/qte77/scrape-stock-kpi/issues/17)
- README rewrite reflecting new architecture — issue [#3](https://github.com/qte77/scrape-stock-kpi/issues/3)

## 0.5.0 — Composite proxy scores

Reproduce Traderfox-style aggregate signals as transparent, formula-documented composites built on 0.4.0's fundamentals.

**Goals:**

- `CompositeScores(BaseModel)` with quality / dividend / growth / big_call / aaqs / hgi proxies; each formula documented in docstrings — issue [#18](https://github.com/qte77/scrape-stock-kpi/issues/18)

## 0.5.0+ — Deferred (revisit after composites ship)

- Long/short hedging strategy: relative-strength + regime-split + ranking — epic [#4](https://github.com/qte77/scrape-stock-kpi/issues/4) with sub-issues [#8](https://github.com/qte77/scrape-stock-kpi/issues/8), [#9](https://github.com/qte77/scrape-stock-kpi/issues/9), [#10](https://github.com/qte77/scrape-stock-kpi/issues/10)

## Open research (no milestone)

- TradingView screener evaluation — issue [#21](https://github.com/qte77/scrape-stock-kpi/issues/21)
- Alternative risk-sentiment sources (UBS, AAII, NAAIM, etc.) — issue [#22](https://github.com/qte77/scrape-stock-kpi/issues/22)
- pandas alternatives (Polars, Dask, Modin, etc.) — issue [#23](https://github.com/qte77/scrape-stock-kpi/issues/23)

## Out of scope

- CDS spreads (paid data only)
- Paid-API integrations (Tiingo, FMP, Alpha Vantage premium, Bloomberg)
- Trade execution (analysis only)
- Repo rename (defer; "scrape-stock-kpi" stays even after Traderfox removal — CNN F&G remains a scrape)
