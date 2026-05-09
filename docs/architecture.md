# Architecture

High-level sketch of modules + data flow. See [`UserStory.md`](UserStory.md) for *what* this builds; this doc covers *how*.

## Principles

- **Modular**: one responsibility per module, narrow public API, no cross-module reach-around
- **OOP-minimal**: prefer functions; classes only for `pydantic.BaseModel` data containers; no inheritance hierarchies
- **Boundary-validated**: every external payload (CLI args, config files, HTTP responses, library returns) parsed into a pydantic model — invalid data fails loudly at the edge
- **Complexity-budgeted**: ruff `C901` cyclomatic ≤ 10; complexipy cognitive ≤ 15; both gate `make validate`

## Modules

```
app/
├── __main__.py            entrypoint: parse CLI -> resolve universe -> per-ticker pipeline -> write results
├── universe.py            resolve_universe(spec) -> list[ticker]; presets in app/assets/universes/*.txt
├── fundamentals.py        fetch_fundamentals(ticker) -> FundamentalsSnapshot; fetch_price_history(ticker, period) -> DataFrame
├── sentiment.py           fetch_fear_greed() -> FearGreedSnapshot
├── composite_scores.py    quality/dividend/growth/big_call/aaqs/hgi(FundamentalsSnapshot) -> 0-100 floats; CompositeScores BaseModel aggregator
├── config/                JSON config (loaded via Defaults / DomCfg pydantic models)
├── assets/                asset universes (preset *.txt), default watchlist
└── utils/
    ├── parse_args.py      CliArgs(BaseSettings) — pydantic-settings CLI + env
    ├── handle_config.py   Defaults.model_validate_json(...), DomCfg.model_validate_json(...)
    └── handle_files.py    save_json(data, path) with mkdir -p; CSV reader for legacy assets
```

## Data flow

```
CLI args  ──► CliArgs(BaseSettings)
                  │
                  ▼
              universe.resolve_universe()
                  │  list[ticker]
                  ▼
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
  fundamentals          (sentiment runs        (RS hedging
   .fetch_fundamentals   independently on       deferred — see
   .fetch_price_history  cron via               roadmap §0.5+)
        │                fear-greed.yaml)
        │                    │
        ▼                    ▼
  FundamentalsSnapshot   FearGreedSnapshot
        │                    │
        ▼                    │
  composite_scores            │
   .quality/.dividend/...     │
        │                    │
        ▼                    ▼
  CompositeScores ────► save_json(merge, results/<date>/<ticker>.json)
```

## Public types (pydantic.BaseModel)

| Type | Module | Role |
|---|---|---|
| `CliArgs(BaseSettings)` | `utils/parse_args.py` | CLI + env input — `cli_parse_args=True` |
| `Defaults`, `DomCfg` | `utils/handle_config.py` | Validate `app/config/*.json` at load |
| `FundamentalsSnapshot` | `fundamentals.py` | Tier 1 KPIs per ticker (Piotroski, ratios, dividend metrics) |
| `FearGreedSnapshot` | `sentiment.py` | CNN F&G fields + sub-indicator timestamps |
| `CompositeScores` | `composite_scores.py` | Tier 3 proxy aggregates (quality/dividend/growth/big_call/aaqs/hgi) |

## External boundaries

- **`yfinance`** — fundamentals + price history; rate-limit risk; tagged `@pytest.mark.network` for live tests
- **`financetoolkit`** — Piotroski + ratio computations; falls back to yfinance financials when no FMP key
- **CNN F&G JSON endpoint** — `production.dataviz.cnn.io/index/fearandgreed/graphdata`; requires `User-Agent`; stdlib `urllib.request`, no extra deps
- **GitHub Actions cron** — daily snapshot of sentiment committed to `results/fear_greed/<DATE>.json`

## What's not here

- Traderfox provider, Playwright, DOM scraping (removed; see [`decisions/0000-remove-traderfox.md`](decisions/0000-remove-traderfox.md))
- Long/short hedging strategy (Mansfield RS, regime split, ranking) — deferred per roadmap
- Paid-data integrations (CDS, Bloomberg) — explicitly out of scope per [`UserStory.md`](UserStory.md)
