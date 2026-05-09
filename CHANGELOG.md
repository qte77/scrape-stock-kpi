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

### Added

- Tooling adoption per qte77 ecosystem conventions: `uv` (replaces Pipfile),
  `ruff` (replaces black + flake8 + isort + pyupgrade), `pyright` (replaces
  mypy), `Makefile` with `validate` target chaining lint + check_types +
  test_cov, `AGENTS.md` + `CLAUDE.md` agent docs, `.claude/settings.json`
  with marketplace plugins (`cc-meta`, `python-dev`, `docs-governance`,
  `commit-helper`, `codebase-tools`, `tdd-core`, `makefile-core`,
  `planning`, `readme-generator`), GitHub Actions `validate.yaml` workflow.
- `[tool.uv].exclude-newer` pinned to 2026-05-08 for reproducible
  dependency resolution.
- `MEMORY.md` and bwrap sandbox phantom block in `.gitignore` (so101
  pattern); `.gitmessage` conventional-commit template tracked.
- `tests/` scaffold with smoke test; pytest + coverage config.
- Earlier: providers for stock data — [Traderfox](https://aktie.traderfox.com)
  KPI, [Portfolio Visualizer](https://www.portfoliovisualizer.com/optimize-portfolio)
  optim. `tqdm` progress bar, `rich` color print/table, asset shuffling,
  `time.perf_counter()` tracing, performance-measuring with delay.

### Changed

- Python 3.9 → 3.12 (`requires-python = ">=3.12,<3.13"`).
- `parse_args()` now returns a `TypedDict` (`CliArgs`) instead of a
  loose `dict[str, str | bool]`; `__main__.py` accesses values by
  explicit key rather than positional `.values()` unpack.
- `_get_results` portfolio-visualizer branch (`get_values_single_url`)
  now returns a dict keyed by `batch_<n>`, matching the multiple-URL
  branch shape.

### Fixed

- File I/O utilities (`handle_files.py`, `handle_assets.py`,
  `handle_config.py`) no longer return Exception objects from `except`
  blocks; errors propagate naturally so callers see the real failure.
- Latent argument-order bug in `get_values_single_url`: `_get_result`
  was being called with `headless` and `timeout` swapped.
- Optional parameter types in `_handle_page_cookies`
  (`cookie_frame: str | None`, `timeout: int | None`).
- 22 pre-existing pyright errors cleared; pyright now gates `make
  validate` and CI.

### Removed

- `Pipfile`, `.flake8`, `.cirrus.yml`, `.bumpversion.cfg`, `make.bat` —
  superseded by uv / ruff / GitHub Actions / no-release-yet (YAGNI).
