# Agent Instructions for scrape-stock-kpi

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
(stocks, ETFs, FX, futures, crypto, indices). `app/__main__.py` resolves a
universe → fetches per-ticker → prints a rich summary table → writes
`results/fundamentals_<UTC>.json`. See
[docs/architecture.md](docs/architecture.md) for the module map.

Active modules:

- `app/__main__.py` — entrypoint
- `app/universe.py` — universe resolver (presets in `app/assets/universes/*.txt`)
- `app/fundamentals.py` — `FundamentalsSnapshot(BaseModel)` + fetchers
- `app/utils/parse_args.py` — `CliArgs(BaseSettings)`
- `app/assets/universes/` — preset ticker lists

## Decision Framework

**Priority order:** User instructions → AGENTS.md → README.md → existing code patterns

**Information sources:**

- Requirements: task description (primary)
- Run/lint/test commands: `make help`
- Project version: `app/__version__.py`
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
  phase) is reserved for the relative-strength hedging epic (#8/#9/#10).
- Tag network-dependent tests with `@pytest.mark.network` (excluded from
  default `make test` via `-m 'not network'`; opt in with `pytest -m network`)

**Post-task:**

- Run `make validate` — must pass (lint + types + complexity + lint_md + tests)
- `make lint_links` — opt-in locally; mandatory in CI via `links-fail-fast.yml`
- Update `CHANGELOG.md` `[Unreleased]` section for non-trivial changes
- Bump `app/__version__.py` only at the end of a feature branch (semver)
