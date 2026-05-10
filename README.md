# RPA Stock KPI

[![version](https://img.shields.io/github/v/tag/qte77/scrape-stock-kpi?label=version&color=blue)](https://github.com/qte77/scrape-stock-kpi/tags)
[![validate](https://github.com/qte77/scrape-stock-kpi/actions/workflows/validate.yaml/badge.svg)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/validate.yaml)
[![Links (Fail Fast)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/links-fail-fast.yml/badge.svg)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/links-fail-fast.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/qte77/scrape-stock-kpi/badge)](https://www.codefactor.io/repository/github/qte77/scrape-stock-kpi)

Library-based stock KPI CLI: per-ticker fundamentals via yfinance plus a
daily CNN Fear & Greed sentiment snapshot. No API keys, no scraping.

## Status

Released — see [CHANGELOG.md](./CHANGELOG.md) for version history.

## TOC

* [Quickstart](#quickstart)
* [Usage](#usage)
* [Data providers](#data-providers)
* [Fundamentals](#fundamentals)
* [Composite proxy scores](#composite-proxy-scores)
* [Sentiment](#sentiment)
* [KPI TODO](#kpi-todo)
* [Packages used](#packages-used)
* [Quality tooling](#quality-tooling)
* [License](#license)

## Quickstart

```bash
make setup_dev                                  # uv sync (default groups: dev + test)
make run UNIVERSE=qte77-watchlist               # fetch fundamentals (results/ JSON)
make run TICKERS=AAPL,MSFT                      # ad-hoc ticker list
make run TICKERS=AAPL SHOW_SCORES=1             # also append composite-score columns
make help                                       # list available recipes
make validate                                   # lint + types + complexity + md + tests
```

## Usage

`make run` resolves a universe, fetches fundamentals for each ticker via
yfinance, prints a CNN Fear & Greed banner plus a rich summary table for
equities and ETFs, and writes all snapshots to
`results/fundamentals_<UTC>.json`.

Universe sources (in priority order):

* `TICKERS=AAPL,MSFT` — inline comma-separated list
* `TICKERS_FILE=path/to/list.txt` — one ticker per line
* `UNIVERSE=<name>` — preset under `src/assets/universes/<name>.txt`
  (`qte77-watchlist`, `dax40`, `crypto-top10`)
* `PERIOD=5y` — reserved for v0.5.0 composites; ignored by fundamentals

CLI args double as env vars with the `SSK_` prefix
(e.g. `SSK_TICKERS=AAPL,MSFT`).

A separate GitHub Actions cron (`fear-greed.yaml`) runs daily at 21:30
UTC and merges the live CNN headline plus ~1y of historical readings
into per-year history files at `results/cnn_fg/YYYY.json`.

## Data providers

* [Yahoo Finance](https://finance.yahoo.com) — fundamentals + price
  history via [yfinance](https://pypi.org/project/yfinance/)
* [CNN Fear & Greed Index](https://edition.cnn.com/markets/fear-and-greed)
  — sentiment headline + 9 subindicators via the public
  `production.dataviz.cnn.io` JSON endpoint (no API key); see
  [`docs/cnn-fg-api.md`](docs/cnn-fg-api.md)

## Fundamentals

`FundamentalsSnapshot` (per ticker, point-in-time):

* **Identity** — symbol, sector, industry, currency, exchange, quoteType
* **Valuation** — market cap, P/E (trailing/forward), P/B, P/S TTM, EV,
  EV/EBITDA
* **Profitability** — ROE, ROA, profit/gross/operating margins
* **Financial health** — debt/equity, current ratio, quick ratio
* **Growth** — revenue growth, earnings growth
* **Dividends** — yield, payout ratio
* **Per-share** — trailing/forward EPS, book value
* **52-week range** — high, low

Sparse snapshots (missing numerics) for non-equities (FX, futures,
crypto) are valid by design.

## Composite proxy scores

Six 0-100 proxy scores computed from each `FundamentalsSnapshot` and
attached to its JSON output:

* **Quality** — mean of normalized ROE, ROA, operating margin, inverted
  D/E (negative-D/E term dropped for distressed balance sheets)
* **Dividend** — yield + payout-ratio sweet-spot at ~50 %
* **Growth** — 1-year revenue and earnings growth (point-in-time
  proxies for CAGR)
* **Big Call** — weighted Quality / Dividend / Growth, reweighted
  proportionally over non-`None` components so a tech stock with no
  dividend still scores
* **AAQS** — Quality combined with low-volatility (low beta is better)
* **HGI** — growth components plus a fixed bonus when operating margin
  clears 10 %

Formulas are simplified relative to the Traderfox originals because
`FundamentalsSnapshot` carries only point-in-time fields. See
[`docs/decisions/0002-simplified-composites.md`](docs/decisions/0002-simplified-composites.md)
for the full trade-off and per-composite formula. Composites are
always computed and persisted; the rich summary table appends Quality
/ Div / Growth columns only with `SHOW_SCORES=1` (off by default to
keep the table readable on 80-column terminals).

## Sentiment

`FearGreedSnapshot` (CNN F&G headline, captured daily):

* **Headline** — score (0-100), rating (`extreme fear` → `extreme
  greed`), timestamp
* **Deltas** — previous close, 1-week, 1-month, 1-year scores
* **Subindicators** — 9 named `SubindicatorReading` entries (S&P
  momentum, breadth, VIX, put/call, junk-bond demand, market momentum,
  safe-haven demand, stock-price strength, market volatility); rating +
  raw value for every day in history, plus a 0-100 score for today only
  (CNN doesn't ship per-day subindicator scores in their `data[]` arrays
  — see [`docs/cnn-fg-api.md`](docs/cnn-fg-api.md))

Per-year files at `results/cnn_fg/YYYY.json` are date-sorted JSON
arrays; today's entry is force-overwritten on every cron run so deltas
and subindicator scores survive intraday CNN updates.

## KPI TODO

* Composite scores (Quality / Dividend / Growth / Big Call / AAQS /
  HGI) — see [#18](https://github.com/qte77/scrape-stock-kpi/issues/18)
* Beta, PEG
* Stock CDS and yield (paid data; out of scope for now)

## Packages used

* [yfinance](https://pypi.org/project/yfinance/) — Yahoo Finance data
* [pydantic](https://pypi.org/project/pydantic/) — typed data models
* [pydantic-settings](https://pypi.org/project/pydantic-settings/) —
  CLI args + env vars
* [rich](https://pypi.org/project/rich/) — console output + tables
* [tqdm](https://pypi.org/project/tqdm/) — progress bars

CNN F&G uses the stdlib `urllib.request` only — no extra dependency.

## Quality tooling

* [uv](https://docs.astral.sh/uv/) — package + venv manager
* [ruff](https://docs.astral.sh/ruff/) — linter + formatter
* [pyright](https://microsoft.github.io/pyright/) — static type checker
* [complexipy](https://pypi.org/project/complexipy/) — cognitive
  complexity gate
* [pytest](https://docs.pytest.org/) +
  [pytest-cov](https://pypi.org/project/pytest-cov/) — tests + coverage
* [markdownlint](https://github.com/igorshubovych/markdownlint-cli) —
  markdown style
* [lychee](https://lychee.cli.rs/) — broken-link checker

## License

[Apache 2.0](LICENSE)
