# RPA Stock KPI

[![version](https://img.shields.io/github/v/tag/qte77/scrape-stock-kpi?label=version&color=blue)](https://github.com/qte77/scrape-stock-kpi/tags)
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

## Universe sources

In priority order:

| Source | Example |
|---|---|
| Inline list | `TICKERS=AAPL,MSFT` |
| File (one symbol per line) | `TICKERS_FILE=path/to/list.txt` |
| Preset | `UNIVERSE=qte77-watchlist` (also `dax40`, `crypto-top10` — see [`src/assets/universes/`](src/assets/universes)) |

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
