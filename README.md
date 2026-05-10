# RPA Stock KPI

[![version](https://img.shields.io/badge/version-0.5.0-blue.svg)](https://github.com/qte77/scrape-stock-kpi/blob/main/CHANGELOG.md)
[![validate](https://github.com/qte77/scrape-stock-kpi/actions/workflows/validate.yaml/badge.svg)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/validate.yaml)
[![Links (Fail Fast)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/links-fail-fast.yml/badge.svg)](https://github.com/qte77/scrape-stock-kpi/actions/workflows/links-fail-fast.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/qte77/scrape-stock-kpi/badge)](https://www.codefactor.io/repository/github/qte77/scrape-stock-kpi)

Library-based stock KPI CLI: per-ticker fundamentals via yfinance plus a
daily CNN Fear & Greed sentiment snapshot. No API keys, no scraping.

## Quickstart

```bash
make setup_dev                              # uv sync (default groups: dev + test)
make run UNIVERSE=qte77-watchlist           # fetch fundamentals -> results/fundamentals_<UTC>.json
make run TICKERS=AAPL,MSFT                  # ad-hoc ticker list
make run TICKERS=AAPL SHOW_SCORES=1         # also append composite-score columns
make help                                   # list available recipes
make validate                               # lint + types + complexity + md + tests
```

CLI args double as env vars with the `SSK_` prefix
(e.g. `SSK_TICKERS=AAPL,MSFT`).

## What it produces

* **Fundamentals** — `results/fundamentals_<UTC>.json`: one
  `FundamentalsSnapshot` per resolved ticker (~30 yfinance fields)
  plus six 0-100 composite proxy scores (Quality / Dividend / Growth
  / Big Call / AAQS / HGI). Sparse fields for non-equities (FX,
  futures, crypto) are valid by design.
* **Sentiment** — `results/cnn_fg/YYYY.json`: per-year date-sorted
  array of CNN Fear & Greed snapshots (headline + 9 subindicators).
  Updated daily by a GitHub Actions cron at 21:30 UTC.

Field shapes live in [`src/fundamentals.py`](src/fundamentals.py),
[`src/composite_scores.py`](src/composite_scores.py), and
[`src/sentiment.py`](src/sentiment.py).

## Sample output

`make run TICKERS=AAPL SHOW_SCORES=1`:

```text
Fear & Greed 66.9 (greed) as of 2026-05-08 23:59 UTC
scrape-stock-kpi resolving 1 tickers
                         Fundamentals (equities & ETFs)
┏━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━┳━━━━━━━━┓
┃ Symbol ┃ Sector ┃  Market ┃   P/E ┃    ROE ┃     Div ┃ Quali… ┃ Div ┃ Growth ┃
┃        ┃        ┃     Cap ┃       ┃        ┃   Yield ┃        ┃     ┃        ┃
┡━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━╇━━━━━━━━┩
│ AAPL   │ Techn… │   4.31T │ 35.47 │ 141.4… │  37.00% │     90 │  63 │     56 │
└────────┴────────┴─────────┴───────┴────────┴─────────┴────────┴─────┴────────┘
Wrote results/fundamentals_2026-05-10T12-16-21Z.json
```

The persisted JSON keeps every field plus the nested composite scores:

```json
{
  "symbol": "AAPL",
  "sector": "Technology",
  "market_cap": 4308095467520.0,
  "trailing_pe": 35.47,
  "return_on_equity": 1.4147,
  "operating_margins": 0.32275,
  "debt_to_equity": 79.548,
  "revenue_growth": 0.166,
  "earnings_growth": 0.218,
  "dividend_yield": 0.37,
  "beta": 1.065,
  "composite_scores": {
    "quality": 90.06,
    "dividend": 62.59,
    "growth": 56.0,
    "big_call": 71.6,
    "aaqs": 68.4,
    "hgi": 66.0
  }
}
```

(Truncated for brevity — every `FundamentalsSnapshot` field is
present.) The "Div Yield 37.00%" you see in the table is the
[#43](https://github.com/qte77/scrape-stock-kpi/issues/43) yfinance
percentage-vs-fraction drift, pending normalization.

## Universe sources

In priority order:

| Source | Example |
|---|---|
| Inline list | `TICKERS=AAPL,MSFT` |
| File (one symbol per line) | `TICKERS_FILE=path/to/list.txt` |
| Preset | `UNIVERSE=qte77-watchlist` (or `crypto-top10` — see [`src/assets/universes/`](src/assets/universes) for all available presets) |

## Documentation

* [`docs/architecture.md`](docs/architecture.md) — module map + data flow
* [`docs/UserStory.md`](docs/UserStory.md) — product intent + non-goals
* [`docs/roadmap.md`](docs/roadmap.md) — milestones + tracked issues
* [`docs/decisions/`](docs/decisions) — ADRs (Traderfox removal,
  `financetoolkit` deferral, simplified composites)
* [`docs/cnn-fg-api.md`](docs/cnn-fg-api.md) — CNN F&G endpoint schema
* [`CHANGELOG.md`](CHANGELOG.md) — release history + known issues
* [`AGENTS.md`](AGENTS.md) — agent collaboration rules

## License

[Apache 2.0](LICENSE)
