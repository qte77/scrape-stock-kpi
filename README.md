# RPA Stock KPI

[![version](https://img.shields.io/badge/version-0.5.1-blue.svg)](https://github.com/qte77/analyze-stock-kpi/blob/main/CHANGELOG.md)
[![validate](https://github.com/qte77/analyze-stock-kpi/actions/workflows/validate.yaml/badge.svg)](https://github.com/qte77/analyze-stock-kpi/actions/workflows/validate.yaml)
[![Links (Fail Fast)](https://github.com/qte77/analyze-stock-kpi/actions/workflows/links-fail-fast.yml/badge.svg)](https://github.com/qte77/analyze-stock-kpi/actions/workflows/links-fail-fast.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/qte77/analyze-stock-kpi/badge)](https://www.codefactor.io/repository/github/qte77/analyze-stock-kpi)
[![CodeQL](https://github.com/qte77/analyze-stock-kpi/actions/workflows/codeql.yaml/badge.svg)](https://github.com/qte77/analyze-stock-kpi/actions/workflows/codeql.yaml)
[![SBOM](https://github.com/qte77/analyze-stock-kpi/actions/workflows/sbom.yaml/badge.svg)](https://github.com/qte77/analyze-stock-kpi/actions/workflows/sbom.yaml)

[![vscode.dev](https://img.shields.io/static/v1?logo=visualstudiocode&label=&message=vscode.dev&labelColor=2c2c32&color=007acc&logoColor=007acc)](https://vscode.dev/github/qte77/analyze-stock-kpi)
[![Codespace Dev](https://img.shields.io/static/v1?logo=visualstudiocode&label=&message=Codespace%20Dev&labelColor=2c2c32&color=007acc&logoColor=007acc)](https://github.com/codespaces/new?repo=qte77/analyze-stock-kpi)

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
analyze-stock-kpi resolving 1 tickers
                         Fundamentals (equities & ETFs)
┏━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━┳━━━━━━━━┓
┃ Symbol ┃ Sector ┃  Market ┃   P/E ┃    ROE ┃     Div ┃ Quali… ┃ Div ┃ Growth ┃
┃        ┃        ┃     Cap ┃       ┃        ┃   Yield ┃        ┃     ┃        ┃
┡━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━╇━━━━━━━━┩
│ AAPL   │ Techn… │   4.31T │ 35.47 │ 141.4… │   0.37% │     90 │  20 │     56 │
└────────┴────────┴─────────┴───────┴────────┴─────────┴────────┴─────┴────────┘
Wrote results/fundamentals_2026-05-11T00-00-00Z.json
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
  "dividend_yield": 0.0037,
  "beta": 1.065,
  "composite_scores": {
    "quality": 90.06,
    "dividend": 20.0,
    "growth": 56.0,
    "big_call": 65.8,
    "aaqs": 68.4,
    "hgi": 66.0
  }
}
```

(Truncated for brevity — every `FundamentalsSnapshot` field is
present.) `dividend_yield` is stored as a fraction; the
`_normalize_yfinance_info` helper divides yfinance's current
percentage-shaped value (`0.37`) at the fetch boundary.

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
