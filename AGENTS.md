# Agent Instructions for analyze-stock-kpi

Behavioral rules for AI agents working on this library-based stock KPI CLI.
For technical details and run instructions, see [README.md](README.md). For
module map and data flow, see [docs/architecture.md](docs/architecture.md).

## Core Rules

- Follow KISS, DRY, YAGNI, AHA — simplest solution that works, no speculative
  features, no premature abstractions
- **Never assume missing context** — ask if uncertain about requirements
- **Never hallucinate libraries** — only use packages verified in `pyproject.toml`
- **Always confirm file paths exist** before referencing in code or tests
- **Never delete existing code** unless explicitly instructed
- **Touch only task-related code** — bug fixes don't need surrounding cleanup
- **Strict pydantic** — every structured payload is a `BaseModel`; CLI/env via
  `BaseSettings(cli_parse_args=True)`. No `TypedDict`, no `dataclass`.

## Architecture Overview

Single-purpose CLI fetching fundamentals via yfinance for any Yahoo symbol
(stocks, ETFs, FX, futures, crypto, indices). `src/__main__.py` prints a
CNN Fear & Greed banner, resolves a universe → fetches per-ticker → prints
a rich summary table → writes `results/fundamentals_<UTC>.json`. Two GHA
crons feed a separate `data` branch (outside the default-branch ruleset
scope) via verified REST Git Data API commits from `actions/github-script`:
`fear-greed.yaml` (daily) merges the CNN F&G headline + ~1y of history
into `results/cnn_fg/YYYY.json`; `demo-snapshot.yml` (weekly) writes one
`results/demo/<UNIVERSE>/YYYY-MM-DD.json` snapshot plus `index.json`
manifest. A third workflow (`gh-pages.yml`) deploys `docs/demo/*` to
GitHub Pages — the page fetches data cross-origin from
raw.githubusercontent.com on the `data` branch. See
[docs/architecture.md](docs/architecture.md) for the module map and
[`docs/decisions/0003-defer-rs-hedging-epic.md`](docs/decisions/0003-defer-rs-hedging-epic.md)
for the v0.6.0 repurposing rationale.

Active modules:

- `src/__main__.py` — entrypoint
- `src/universe.py` — universe resolver (presets in `src/assets/universes/*.txt`)
- `src/fundamentals.py` — `FundamentalsSnapshot(BaseModel)` + fetchers
- `src/sentiment.py` — `FearGreedSnapshot(BaseModel)` + CNN F&G fetcher
- `src/utils/parse_args.py` — `CliArgs(BaseSettings)`
- `src/assets/universes/` — preset ticker lists
- `scripts/build_demo_manifest.py` — stdlib-only manifest builder for
  `results/demo/<UNIVERSE>/index.json` (called by `demo-snapshot.yml`)
- `docs/demo/{index.html,app.js,style.css}` — static dashboard sources

## Decision Framework

**Priority order:** User instructions → AGENTS.md → README.md → existing code patterns

**Information sources:**

- Requirements: task description (primary)
- Run/lint/test commands: `make help`
- Project version: `src/__version__.py`
- Library API shapes (yfinance, pydantic, etc.): `context7` MCP, not training data

**Anti-scope-creep:** Implement only what is explicitly requested. Prefer
landing small working slices over comprehensive rewrites within a single PR.

## Quality Thresholds

Subjective gut-check before starting any task. If below threshold: gather
more context or ask the user.

- **Context** 8/10 — understand requirements, codebase patterns, target API
- **Clarity** 7/10 — clear implementation path and expected outcomes
- **Alignment** 8/10 — follows project patterns, respects KISS/DRY/YAGNI/AHA
- **Success** 7/10 — confident in completing task correctly

## Agent Quick Reference

**Pre-task:**

- Read AGENTS.md → README.md → relevant `docs/` files
- Confirm quality thresholds met
- Check `make help` for available recipes

**During task:**

- Use `make` commands; document any deviation
- For new feature code: **topic-grouped commits with tests + implementation
  co-committed**. Strict TDD (Red → Green → Refactor with one commit per
  phase) was reserved for the relative-strength hedging epic, now
  deferred — see [`docs/decisions/0003-defer-rs-hedging-epic.md`](docs/decisions/0003-defer-rs-hedging-epic.md).
- Tag network-dependent tests with `@pytest.mark.network` (excluded from
  default `make test` via `-m 'not network'`; opt in with `pytest -m network`)
- **GHA workflows**: pin every `uses:` to a full-length commit SHA per
  the repo's "Require actions to be pinned to a full-length commit SHA"
  rule. Resolve via `gh api /repos/<owner>/<repo>/git/ref/tags/<tag>`
  and dereference annotated tags via `gh api .../git/tags/<sha>`.
- **Bot commits to `main` are blocked** by the `required_signatures` +
  `pull_request` rules. Workflows that need to commit data must target
  the `data` branch via the verified-commit pattern
  (`actions/github-script` calling REST Git Data API: Blob → Tree →
  Commit → Ref). See `demo-snapshot.yml` and `fear-greed.yaml` for the
  template.

**Post-task:**

- Run `make validate` — must pass (lint + types + complexity + lint_md + tests)
- `make lint_links` — opt-in locally; mandatory in CI via `links-fail-fast.yml`
- Update `CHANGELOG.md` `[Unreleased]` section for non-trivial changes
- Bump `src/__version__.py` only at the end of a feature branch (semver)
