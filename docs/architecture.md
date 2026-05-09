# Architecture

High-level sketch of modules + data flow. See [`UserStory.md`](UserStory.md) for *what* this builds; this doc covers *how*.

## Principles

- **Modular**: one responsibility per module, narrow public API, no cross-module reach-around
- **OOP-minimal**: prefer functions; classes only for `pydantic.BaseModel` data containers; no inheritance hierarchies
- **Boundary-validated**: every external payload (CLI args, HTTP responses, library returns) parsed into a pydantic model — invalid data fails loudly at the edge
- **Complexity-budgeted**: ruff `C901` cyclomatic ≤ 10; complexipy cognitive ≤ 15; both gate `make validate`

## Modules

```text
app/
├── __main__.py            entrypoint: resolve universe -> per-ticker fetch -> rich table + results/fundamentals_<UTC>.json
├── universe.py            resolve_universe(args) -> list[ticker]; presets in app/assets/universes/*.txt
├── fundamentals.py        fetch_fundamentals(ticker) -> FundamentalsSnapshot
│                          fetch_price_history(ticker, period) -> DataFrame
│                          fetch_universe_fundamentals(tickers) -> list[FundamentalsSnapshot]
├── sentiment.py           fetch_fear_greed() -> FearGreedSnapshot     [v0.4.0 / #17 — not yet implemented]
├── composite_scores.py    quality/dividend/growth/big_call/aaqs/hgi   [v0.5.0 / #18 — not yet implemented]
├── assets/
│   └── universes/         preset *.txt ticker lists (one per universe name)
└── utils/
    └── parse_args.py      CliArgs(BaseSettings) — pydantic-settings CLI + env (env_prefix="SSK_")
```

## Data flow (v0.4.0 current)

```text
CLI args  ──► CliArgs(BaseSettings)
                  │
                  ▼
            universe.resolve_universe()
                  │  list[ticker]
                  ▼
        fundamentals.fetch_universe_fundamentals()
                  │  list[FundamentalsSnapshot]   (sequential, tqdm, per-ticker errors logged + skipped)
                  ▼
   rich table (equities + ETFs only)  +  json.dumps -> results/fundamentals_<UTC>.json
```

v0.5.0 additions (deferred): `sentiment.fear_greed` runs on a separate cron workflow; `composite_scores` aggregates `FundamentalsSnapshot` fields into 0-100 proxy scores merged into per-asset output.

## Public types (`pydantic.BaseModel`)

| Type | Module | Role |
|---|---|---|
| `CliArgs(BaseSettings)` | `utils/parse_args.py` | CLI + env input — `cli_parse_args=True`, `extra="forbid"` |
| `FundamentalsSnapshot` | `fundamentals.py` | Per-ticker fundamentals — ~30 aliased fields; sparse for non-equities |
| `FearGreedSnapshot` | `sentiment.py` | CNN F&G fields — *v0.4.0 / #17, not yet implemented* |
| `CompositeScores` | `composite_scores.py` | Quality/dividend/growth/big_call/aaqs/hgi proxies — *v0.5.0 / #18, not yet implemented* |

## External boundaries

- **`yfinance`** — fundamentals (`Ticker.info`) + price history (`Ticker.history`); rate-limit risk; live tests tagged `@pytest.mark.network` (excluded from default `make test`, opt in via `pytest -m network`)
- **CNN F&G JSON endpoint** *(v0.4.0 / #17)* — `production.dataviz.cnn.io/index/fearandgreed/graphdata`; requires `User-Agent` header; stdlib `urllib.request`, no extra deps
- **GitHub Actions cron** *(v0.4.0 / #17)* — daily snapshot of sentiment committed to `results/fear_greed/<DATE>.json`
- **`financetoolkit`** — *deferred to v0.5.0 (#18); see [`decisions/0001-defer-financetoolkit.md`](decisions/0001-defer-financetoolkit.md)*

## What's not here

- Traderfox provider, Playwright, DOM scraping (removed; see [`decisions/0000-remove-traderfox.md`](decisions/0000-remove-traderfox.md))
- Long/short hedging strategy (Mansfield RS, regime split, ranking) — deferred per roadmap §0.5+
- Paid-data integrations (CDS, Bloomberg, FMP) — explicitly out of scope per [`UserStory.md`](UserStory.md)
