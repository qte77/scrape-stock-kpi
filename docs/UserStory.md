# User Story

## What this is

A no-API-keys CLI that produces a per-asset KPI dossier (fundamentals + sentiment + composite scores) for any tradable Yahoo symbol — stocks, ETFs, FX pairs, commodity futures, crypto, indices.

## Who it is for

Solo investors building their own auditable, rule-based screening pipeline. Anyone who wants Traderfox-style aggregate scores without paying Traderfox, with formulas they can read and modify.

## Core user stories

- **As an investor**, I want to point the tool at a list of tickers (or a curated universe preset) and get one JSON snapshot per asset so I can sort/filter on KPIs in any downstream tool.
- **As an investor**, I want quality / dividend / growth / robustness composite scores derived from documented public formulas (Piotroski, ROIC stability, dividend coverage, CAGR) so I can audit and tune the weighting myself.
- **As an investor**, I want a daily CNN Fear & Greed sentiment snapshot committed to the repo so I have a long-running market-mood timeseries without paying for one.
- **As a maintainer**, I want every structured payload validated by pydantic and every module within strict cyclomatic + cognitive complexity budgets so the codebase stays readable and the failure modes are loud.

## Non-goals (explicit)

- Replicate Traderfox's exact proprietary numerical scores (won't match byte-for-byte; composite proxies are documented approximations of the same signals)
- Long/short hedging strategy execution (deferred — see roadmap §0.5+ and issues #4 / #8 / #9 / #10)
- Paid-data integrations (CDS spreads, Bloomberg, Refinitiv) — out of scope
- Automated trade execution — analysis only

## v0.4.0 done means (current milestone)

- `make run UNIVERSE=<preset>` (or `TICKERS=...`, `TICKERS_FILE=...`) writes a single `results/fundamentals_<UTC>.json` containing one `FundamentalsSnapshot` per resolved ticker. Sparse fields for non-equities are valid.
- Stdout shows a rich summary table for equities + ETFs in the resolved universe.
- CNN F&G snapshot lands daily in `results/fear_greed/<DATE>.json` via cron after #17 ships.
- `make validate` passes lint + types + complexity + lint_md + tests. CI green on push and PR (validate + links-fail-fast workflows).

## v1.0.0 vision (post v0.5.0)

`make run UNIVERSE=<preset>` produces, per asset in `results/<DATE>_<universe>/<ticker>/`:

- `fundamentals.json` — Tier 1: extends v0.4.0's `FundamentalsSnapshot` with Piotroski, ROIC, Beta, PEG, dividend-aristocrat flag (additions land via v0.5.0 #18 and later)
- `composites.json` — Tier 3: quality / dividend / growth / big_call / aaqs / hgi proxy scores (v0.5.0 #18)
- `sentiment.json` — CNN F&G snapshot (v0.4.0 #17, runs independently on cron)

The per-asset directory layout is a future schema change from v0.4.0's single-file output; not yet implemented.
