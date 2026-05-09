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

## Done means

`make run UNIVERSE=<preset>` produces, per asset in `results/<DATE>_<universe>/`:
- `fundamentals.json` (Tier 1: Piotroski, ROE/ROA/ROIC, Beta, PEG, margin, E/P, yield, aristocrat flag)
- `composites.json` (Tier 3: quality / dividend / growth / big_call / aaqs / hgi proxy scores)
- `sentiment.json` (CNN F&G snapshot, daily-cron-committed independently)

`make validate` passes lint + types + tests + complexity. CI green.
