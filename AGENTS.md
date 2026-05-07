# Agent Instructions for scrape-stock-kpi

Behavioral rules for AI agents working on this Playwright-based stock KPI
scraper. For technical details and run instructions, see [README.md](README.md).

## Core Rules

- Follow KISS, DRY, YAGNI, AHA — simplest solution that works, no speculative
  features, no premature abstractions
- **Never assume missing context** — ask if uncertain about requirements
- **Never hallucinate libraries** — only use packages verified in `pyproject.toml`
- **Always confirm file paths exist** before referencing in code or tests
- **Never delete existing code** unless explicitly instructed
- **Touch only task-related code** — bug fixes don't need surrounding cleanup

## Architecture Overview

Single-purpose CLI scraper. `app/__main__.py` orchestrates: load defaults +
DOM config + asset list, then dispatch to a provider scraper that visits each
URL with Playwright, extracts KPI values via DOM selectors, computes averages,
and writes JSON results.

- `app/app.py` — provider dispatch (`get_values_wrapper`, `calculate_averages_wrapper`)
- `app/utils/handle_playwright.py` — browser automation
- `app/utils/handle_*.py` — assets, config, data, files I/O
- `app/config/` — `defaults.json` (paths, timeouts, base URLs) and `dom.json`
  (per-provider DOM selectors)
- `app/assets/` — asset CSVs (prod + test)

## Decision Framework

**Priority order:** User instructions → AGENTS.md → README.md → existing code patterns

**Information sources:**

- Requirements: task description (primary)
- Run/lint/test commands: `make help`
- Project version + author: `app/__version__.py`
- Provider DOM contracts: `app/config/dom.json`

**Anti-scope-creep:** Implement only what is explicitly requested. The repo is
DRAFT/WIP — prefer landing small working slices over comprehensive rewrites.

## Quality Thresholds

Before starting any task:

- **Context**: 8/10 — understand requirements, codebase patterns, scraping target
- **Clarity**: 7/10 — clear implementation path and expected outcomes
- **Alignment**: 8/10 — follows project patterns, respects KISS/DRY/YAGNI/AHA
- **Success**: 7/10 — confident in completing task correctly

If below threshold: gather more context or ask the user.

## Agent Quick Reference

**Pre-task:**

- Read AGENTS.md → README.md
- Confirm quality thresholds met
- Check `make help` for available recipes

**During task:**

- Use `make` commands; document any deviation
- For new feature code: follow TDD (Red → Green → Refactor) with one commit
  per phase
- Tag network-dependent tests with `@pytest.mark.network`,
  Playwright-dependent tests with `@pytest.mark.playwright`

**Post-task:**

- Run `make validate` — must pass
- Update CHANGELOG.md `[Unreleased]` section for non-trivial changes
- Bump `app/__version__.py` only at the end of a feature branch (semver)
