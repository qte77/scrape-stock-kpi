# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Types of changes:

- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bugfixes.
- `Security` in case of vulnerabilities.

## [Unreleased]

v0.4.0 in flight: replaces the Traderfox scraper with a library-based
fundamentals + sentiment + composites stack. See
`docs/decisions/0000-remove-traderfox.md`.

### Added

- `app/sentiment.py` — `FearGreedSnapshot(BaseModel)`, `fetch_fear_greed()`,
  `parse_historical()`, and `merge_payload_into_years()` via stdlib
  `urllib.request`. CNN's WAF requires a current desktop-browser UA +
  `Accept` + `Referer: https://edition.cnn.com/` (returns 418 otherwise);
  all three are sent. Each daily entry now also carries a
  `subindicators: dict[str, SubindicatorReading]` map covering CNN's 9
  subindicator blocks (S&P momentum, breadth, VIX, etc.). Today's row
  has the precise 0-100 score per subindicator; historical rows have
  rating + raw value but no per-day score (CNN doesn't ship that). See
  [`docs/cnn-fg-api.md`](docs/cnn-fg-api.md) for the backfillable-vs-
  daily-only breakdown. `python -m app.sentiment` merges the live
  headline + ~1y of historical readings into per-year JSON files at
  `results/cnn_fg/YYYY.json` (sorted by date; today's entry is force-
  overwritten with the live headline so its `previous_*` deltas and
  per-subindicator scores survive intraday CNN updates) (#17).
- `.github/workflows/fear-greed.yaml` — daily cron at 21:30 UTC (~30 min
  after NYSE close, year-round) plus `workflow_dispatch`; commits the
  rewritten year files via `stefanzweifel/git-auto-commit-action@v5`,
  scoped to `results/cnn_fg/[0-9][0-9][0-9][0-9].json` (#17).
- `app/fundamentals.py` — `FundamentalsSnapshot(BaseModel)` plus
  `fetch_fundamentals` / `fetch_price_history` /
  `fetch_universe_fundamentals`. yfinance-backed, ~30 aliased fields,
  sparse snapshots for non-equities (FX/futures/crypto) valid by design
  (#28, closes #16, supersedes #7).
- `app/__main__.py` wires fundamentals end-to-end: fetch every resolved
  ticker, print a rich summary table (equities + ETFs), persist all
  snapshots to `results/fundamentals_<UTC>.json` (#28).
- `app/universe.py` — universe resolver with presets in
  `app/assets/universes/`, CSV/file/inline ticker sources, dedup with
  order preservation (#26, closes #20).
- `app/utils/parse_args.py` — `CliArgs(BaseSettings)` typed CLI args + env
  vars (env prefix `SSK_`, kebab-case CLI flags, `extra="forbid"`); adds
  `period` field reserved for the v0.5.0 composites PR (#26, #28).
- Governance scaffold: `docs/architecture.md`, `docs/UserStory.md`,
  `docs/roadmap.md`, `docs/decisions/0000-remove-traderfox.md` (#24);
  `docs/decisions/0001-defer-financetoolkit.md` documents the v0.4.0
  yfinance-only scope amendment.
- Complexity gates: `complexipy` cognitive ≤15 + `ruff` mccabe ≤10, both
  wired into `make validate` and CI (#24).
- Mandatory markdown + link checks: `lint_md` (in `make validate` and CI),
  `lint_links` (CI workflow `links-fail-fast.yml` runs on push/PR/weekly).
  Adopts the qte77 Agents-eval convention; `.lychee.toml` cribbed from
  sibling `llm-local-text` (#27, #28).
- Dependencies: `pydantic>=2.10`, `pydantic-settings>=2.6` (#26),
  `yfinance>=0.2.40` (#28).

### Changed

- `make run` no longer scrapes via Playwright; runs fundamentals via
  yfinance and writes `results/fundamentals_<UTC>.json` plus a rich
  summary table (#28). A CNN Fear & Greed banner now precedes the table;
  fetch failure logs a warning and continues (#17).
- `results/` is no longer gitignored — cron-committed F&G snapshots live
  under `results/cnn_fg/`. The cron's `file_pattern` is scoped narrowly
  so locally-produced fundamentals files are never accidentally swept
  into a CI commit (#17).
- Default `pytest` excludes `@pytest.mark.network` tests via
  `-m 'not network'` in addopts. Opt in with `pytest -m network`
  (#28).
- `markdownlint` style: ATX headings via `.markdownlint.json` matching
  the qte77 ecosystem convention from sibling `llm-local-text` (#27).
- Python 3.9 → 3.12 (`requires-python = ">=3.12,<3.13"`).

### Removed

- Traderfox provider end-to-end: `app/utils/handle_playwright.py`,
  `app/config/dom.json`, the Playwright dependency, traderfox dispatch
  in `__main__.py` (#25, closes #19).
- Dead config layer left over from the Traderfox era:
  `app/utils/handle_config.py`, `app/utils/handle_files.py`,
  `app/config/defaults.json`, the now-empty `app/config/` directory
  (#28).
- `Pipfile`, `.flake8`, `.cirrus.yml`, `.bumpversion.cfg`, `make.bat`
  — superseded by uv / ruff / GitHub Actions / no-release-yet (YAGNI).

### Fixed

- Runtime orphan `title=` kwarg on Playwright page calls and missing
  `mkdir -p results/` before write (#15).
- File I/O utilities no longer return `Exception` objects from
  `except` blocks; errors propagate naturally so callers see the real
  failure (later removed entirely in #28).
- Latent argument-order bug in `get_values_single_url`: `_get_result`
  was called with `headless` and `timeout` swapped (later removed via
  the Traderfox decommission in #25).
- 22 pre-existing pyright errors cleared; pyright gates `make validate`
  and CI.

### Earlier

Pre-Phase-1 setup work — kept here for traceability.

- Tooling adoption per qte77 ecosystem conventions: `uv` (replaces
  Pipfile), `ruff` (replaces black + flake8 + isort + pyupgrade),
  `pyright` (replaces mypy), `Makefile` with `validate` target,
  `AGENTS.md` + `CLAUDE.md` agent docs, `.claude/settings.json` with
  marketplace plugins, GitHub Actions `validate.yaml` workflow.
- `[tool.uv].exclude-newer` pinned for reproducible dependency
  resolution.
- `MEMORY.md` and bwrap sandbox phantom block in `.gitignore`;
  `.gitmessage` conventional-commit template tracked.
- `tests/` scaffold with smoke test; pytest + coverage config.
