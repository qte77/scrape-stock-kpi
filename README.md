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
uv run playwright install chromium              # one-time browser install
make run PROVIDER=traderfox MODE=test HEADLESS=1  # run the scraper (results/ JSON)
make help                                       # list available recipes
make validate                                   # lint + type check + tests with coverage
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

* [Traderfox](https://aktie.traderfox.com)

## KPI

* Traderfox
  * Checks: Quality, Dividend, Growth, Robustness (The Big Call)
  * Piotroski F-Score, AAQS, Dividend Aristocrats, High Growth

## KPI TODO

* [CNN Fear and Greed Index](https://edition.cnn.com/markets/fear-and-greed) scraper
* Stock CDS and yield
* ROI, ROE, ROA
* Beta, PEG
* Profit margin/return on sales
* Earnings-price ratio

## Packages used

* [playwright](https://pypi.org/project/playwright/) — browser automation
* [rich](https://pypi.org/project/rich/) — console output + tables
* [tqdm](https://pypi.org/project/tqdm/) — progress bars

Planned for relative-strength feature (see [#4](https://github.com/qte77/scrape-stock-kpi/issues/4)):

* [yfinance](https://pypi.org/project/yfinance/)
* [QuantStats](https://pypi.org/project/QuantStats/)

## Quality tooling

* [uv](https://docs.astral.sh/uv/) — package + venv manager
* [ruff](https://docs.astral.sh/ruff/) — linter + formatter
* [pyright](https://microsoft.github.io/pyright/) — static type checker
* [pytest](https://docs.pytest.org/) + [pytest-cov](https://pypi.org/project/pytest-cov/) — tests + coverage

## Other possible packages

* [yahoofinancials](https://pypi.org/project/yahoofinancials/)
* [fundamentalanalysis](https://pypi.org/project/fundamentalanalysis/)
* [Quandl](https://pypi.org/project/world-bank-data/)
* [fredapi](https://pypi.org/project/world-bank-data/)
* [world_bank_data](https://pypi.org/project/world-bank-data/)
* [PyPortfolioOpt](https://pypi.org/project/pyportfolioopt/)

## API

* [Alpha Vantage](https://www.alphavantage.co/documentation/)
