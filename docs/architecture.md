# Architecture

High-level sketch of modules + data flow. See [`UserStory.md`](UserStory.md) for *what* this builds; this doc covers *how*.

## Principles

- **Modular**: one responsibility per module, narrow public API, no cross-module reach-around
- **OOP-minimal**: prefer functions; classes only for `pydantic.BaseModel` data containers; no inheritance hierarchies
- **Boundary-validated**: every external payload (CLI args, HTTP responses, library returns) parsed into a pydantic model — invalid data fails loudly at the edge
- **Complexity-budgeted**: ruff `C901` cyclomatic ≤ 10; complexipy cognitive ≤ 15; both gate `make validate`

## Modules

```text
src/
├── __main__.py            entrypoint: resolve universe -> per-ticker fetch -> rich table + results/fundamentals_<UTC>.json
├── universe.py            resolve_universe(args) -> list[ticker]; presets in src/assets/universes/*.txt
├── fundamentals.py        fetch_fundamentals(ticker) -> FundamentalsSnapshot
│                          fetch_price_history(ticker, period) -> DataFrame
│                          fetch_universe_fundamentals(tickers) -> list[FundamentalsSnapshot]
├── sentiment.py           fetch_fear_greed() -> FearGreedSnapshot; `python -m src.sentiment` merges headline + ~1y history into per-year files results/cnn_fg/YYYY.json (sorted JSON arrays, upsert-by-date)
├── composite_scores.py    quality/dividend/growth/big_call/aaqs/hgi 0-100 proxies; `compute_scores(snap) -> CompositeScores`
├── assets/
│   └── universes/         preset *.txt ticker lists (one per universe name)
└── utils/
    └── parse_args.py      CliArgs(BaseSettings) — pydantic-settings CLI + env (env_prefix="SSK_")
```

## Data flow (v0.5.0 current)

```text
CLI args  ──► CliArgs(BaseSettings)
                  │
                  ▼
            sentiment.fetch_fear_greed()  ──► rich banner (best-effort; failure logs and continues)
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

A separate daily GitHub Actions cron (`.github/workflows/fear-greed.yaml`) runs `python -m src.sentiment`, which loads each affected per-year history file (`results/cnn_fg/YYYY.json` — a date-sorted JSON array), upserts the live headline (force, since CNN updates intraday) plus any historical points CNN now exposes that are missing or stale on disk, and rewrites only the year files that changed. The workflow checks out the `data` branch (not `main`) so accumulated history is present before `sentiment.py` merges, then commits the changed year files via the REST Git Data API (Blob → Tree → Commit → Ref) invoked from `actions/github-script@v9`. Commits created via this API path with the workflow's `GITHUB_TOKEN` are signed by GitHub's web-flow PGP key and marked `verified: true` — required by the repo's `required_signatures` ruleset on `main`. The `data` branch lives outside the ruleset's `~DEFAULT_BRANCH` scope, so direct pushes to it succeed.

A second cron (`.github/workflows/demo-snapshot.yml`, Sunday 06:15 UTC) runs `make run UNIVERSE=qte77-watchlist`, renames the timestamped output to `results/demo/qte77-watchlist/YYYY-MM-DD.json`, rebuilds the manifest via `scripts/build_demo_manifest.py`, and commits both files to the `data` branch through the same verified-commit mechanism.

A third workflow (`.github/workflows/gh-pages.yml`) deploys the static dashboard at `docs/demo/{index.html, app.js, style.css}` to GitHub Pages via `actions/upload-pages-artifact` + `actions/deploy-pages` whenever those files change. The dashboard fetches data files at runtime cross-origin from `raw.githubusercontent.com/qte77/analyze-stock-kpi/data/results/…`; this decouples data-update cadence from page deploys.

v0.5.0 attaches a `CompositeScores` object to every `FundamentalsSnapshot` after fetch via `model_copy(update={"composite_scores": compute_scores(snap)})`. The rich summary table appends Quality / Div / Growth columns only when `--show-scores` is passed; persistence carries the composites unconditionally.

## Public types (`pydantic.BaseModel`)

| Type | Module | Role |
|---|---|---|
| `CliArgs(BaseSettings)` | `utils/parse_args.py` | CLI + env input — `cli_parse_args=True`, `extra="forbid"` |
| `FundamentalsSnapshot` | `fundamentals.py` | Per-ticker fundamentals — ~30 aliased fields; sparse for non-equities |
| `FearGreedSnapshot` | `sentiment.py` | CNN F&G headline (score, rating, timestamp, prev close/1w/1m/1y) + optional `subindicators` map of 9 named `SubindicatorReading` entries (score, rating, raw_value); see [`cnn-fg-api.md`](cnn-fg-api.md) for what's backfillable vs daily-only |
| `CompositeScores` | `composite_scores.py` | Quality/dividend/growth/big_call/aaqs/hgi 0-100 proxies derived from `FundamentalsSnapshot`; simplified formulas per [`decisions/0002-simplified-composites.md`](decisions/0002-simplified-composites.md) |

## External boundaries

- **`yfinance`** — fundamentals (`Ticker.info`) + price history (`Ticker.history`); rate-limit risk; live tests tagged `@pytest.mark.network` (excluded from default `make test`, opt in via `pytest -m network`). `_normalize_yfinance_info` in `src/fundamentals.py` divides the current percentage-shaped `info["dividendYield"]` by 100 at the fetch boundary so the rest of the codebase sees fractional yields.
- **CNN F&G JSON endpoint** — `production.dataviz.cnn.io/index/fearandgreed/graphdata`; requires browser-shape headers (UA + `Accept` + `Referer`; returns 418 otherwise); stdlib `urllib.request`, no extra deps. Observed schema in [`cnn-fg-api.md`](cnn-fg-api.md).
- **GitHub Actions cron** — `.github/workflows/fear-greed.yaml` (daily 21:30 UTC) commits per-year history files `results/cnn_fg/YYYY.json`; `.github/workflows/demo-snapshot.yml` (Sunday 06:15 UTC) commits per-week universe snapshots under `results/demo/<UNIVERSE>/`. Both target the `data` branch via verified REST Git Data API commits from `actions/github-script@v9`.
- **`financetoolkit`** — *not used; v0.5.0 composites use simplified formulas with point-in-time `FundamentalsSnapshot` inputs only. See [`decisions/0001-defer-financetoolkit.md`](decisions/0001-defer-financetoolkit.md) and [`decisions/0002-simplified-composites.md`](decisions/0002-simplified-composites.md).*

## What's not here

- Traderfox provider, Playwright, DOM scraping (removed; see [`decisions/0000-remove-traderfox.md`](decisions/0000-remove-traderfox.md))
- Long/short hedging strategy (Mansfield RS, regime split, ranking) — deferred per roadmap §0.5+
- Paid-data integrations (CDS, Bloomberg, FMP) — explicitly out of scope per [`UserStory.md`](UserStory.md)
