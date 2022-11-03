Changelog
===

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

[Unreleased]
---

### Added

- Providers for Stockdata
  - [Traderfox KPI](https://aktie.traderfox.com)
  - [Onvista KPI](https://onvista.de)
  - [Portfolio Visualizer Optim](https://www.portfoliovisualizer.com/optimize-portfolio)
- `tqdm`for progress bar
- `time.perf_counter()` for time tracing
- `rich` for color print and table
- Github action `dependabot.yml` and workflow `links-fail-fast.yml`
- `cirrus.yml` for base CI/CD
- Base linter for markdown and yaml
- Shuffling of input assets and alpha sort of output results
- Performance measuring includes delay
