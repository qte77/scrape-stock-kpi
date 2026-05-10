# RPA Stock KPI

![version](https://img.shields.io/badge/version-0.2.0-blue)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![validate](https://github.com/qte77/scrape-stock-kpi/actions/workflows/validate.yaml/badge.svg)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/validate.yaml)
[![CodeFactor](https://www.codefactor.io/repository/github/qte77/scrape-stock-kpi/badge)](https://www.codefactor.io/repository/github/qte77/scrape-stock-kpi)
[![Links (Fail Fast)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/links-fail-fast.yml/badge.svg)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/links-fail-fast.yml)

Scrape the web for stock KPI without API-keys.

## Status

**[DRAFT]** **[WIP]** **----> Not fully implemented yet**

The current version is <0.0.0>. For version history have a look at [CHANGELOG.md](./CHANGELOG.md).

## Quickstart

```bash
make setup_dev                                  # uv sync (default groups: dev + test)
make run UNIVERSE=qte77-watchlist               # fetch fundamentals (results/ JSON)
make run TICKERS=AAPL,MSFT                      # ad-hoc ticker list
make help                                       # list available recipes
make validate                                   # lint + types + complexity + md + tests
```

<!--
## TOC

* [Usage](#usage-)
* [Install](#install-)
* [Reason](#reason-)
* [Purpose](#purpose-)
* [Paradigms](#paradigms-)
* [App Structure](#app-structure-)
* [App Details](#app-details-)
* [TODO](#todo-)
* [Inspirations](#inspirations-)
* [Rescources](#resources-)

## Usage [↑](#rpa-stock-kpi)

-->

## Data providers

* [Yahoo Finance](https://finance.yahoo.com) — via [yfinance](https://pypi.org/project/yfinance/)

## KPI

`FundamentalsSnapshot` (per ticker, point-in-time):

* **Identity** — symbol, sector, industry, currency, exchange, quoteType
* **Valuation** — market cap, P/E (trailing/forward), P/B, P/S TTM, EV, EV/EBITDA
* **Profitability** — ROE, ROA, profit/gross/operating margins
* **Financial health** — debt/equity, current ratio, quick ratio
* **Growth** — revenue growth, earnings growth
* **Dividends** — yield, payout ratio
* **Per-share** — trailing/forward EPS, book value
* **52-week range** — high, low

Sparse snapshots (missing numerics) for non-equities (FX, futures, crypto)
are valid by design.

## KPI TODO

* [CNN Fear and Greed Index](https://edition.cnn.com/markets/fear-and-greed) — see [#17](https://github.com/qte77/scrape-stock-kpi/issues/17)
* Composite scores (Quality / Dividend / Growth / Big Call / AAQS / HGI) — see [#18](https://github.com/qte77/scrape-stock-kpi/issues/18)
* Beta, PEG
* Stock CDS and yield (paid data; out of scope for now)

## Packages used

* [yfinance](https://pypi.org/project/yfinance/) — Yahoo Finance data
* [pydantic](https://pypi.org/project/pydantic/) — typed data models
* [pydantic-settings](https://pypi.org/project/pydantic-settings/) — CLI args + env vars
* [rich](https://pypi.org/project/rich/) — console output + tables
* [tqdm](https://pypi.org/project/tqdm/) — progress bars

## Quality tooling

* [uv](https://docs.astral.sh/uv/) — package + venv manager
* [ruff](https://docs.astral.sh/ruff/) — linter + formatter
* [pyright](https://microsoft.github.io/pyright/) — static type checker
* [complexipy](https://pypi.org/project/complexipy/) — cognitive complexity gate
* [pytest](https://docs.pytest.org/) + [pytest-cov](https://pypi.org/project/pytest-cov/) — tests + coverage
* [markdownlint](https://github.com/igorshubovych/markdownlint-cli) — markdown style
* [lychee](https://lychee.cli.rs/) — broken-link checker

## Other possible packages

* [yahoofinancials](https://pypi.org/project/yahoofinancials/)
* [fundamentalanalysis](https://pypi.org/project/fundamentalanalysis/)
* [Quandl](https://pypi.org/project/world-bank-data/)
* [fredapi](https://pypi.org/project/world-bank-data/)
* [world_bank_data](https://pypi.org/project/world-bank-data/)
* [PyPortfolioOpt](https://pypi.org/project/pyportfolioopt/)

## API

* [Alpha Vantage](https://www.alphavantage.co/documentation/)
