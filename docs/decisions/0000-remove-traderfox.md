# ADR-0000 — Remove Traderfox scraper, adopt library-based KPIs

**Status:** Accepted (2026-05-09)

**Drives:** [#19](https://github.com/qte77/scrape-stock-kpi/issues/19) (decommission), [#16](https://github.com/qte77/scrape-stock-kpi/issues/16) (fundamentals replacement), [#17](https://github.com/qte77/scrape-stock-kpi/issues/17) (sentiment), [#18](https://github.com/qte77/scrape-stock-kpi/issues/18) (composite proxies)

## Context

The repo's original architecture scraped [Traderfox](https://aktie.traderfox.com) via Playwright, clicking through DOM tabs to extract eight per-asset scores: Quality, Dividend, Growth, Robustness (Big Call), Piotroski F-Score, AAQS, Dividend Aristocrats, High Growth Index. Six of those eight are Traderfox-proprietary aggregates with undocumented weights.

## Problem

1. **Fragility** — Traderfox redesigns the DOM periodically; selectors in `app/config/dom.json` rot silently and crash the run loop. No anti-bot defenses.
2. **Opacity** — six of eight scores are proprietary black boxes. We can't audit, replicate, or tune them.
3. **Dependency weight** — Playwright requires a Chromium download (`playwright install`) on every CI run and dev environment, plus headful/headless complexity.
4. **Coverage gap** — Traderfox is German-investor-focused; misses ETFs, FX, commodities, crypto entirely. The README's KPI list (and the user's own use cases) implies broader asset coverage.
5. **Single point of failure** — one provider, one scraper, one DOM contract.

## Decision

Replace the Traderfox scraper with a library-based KPI pipeline:

- **Fundamentals**: `yfinance` (raw financials, prices) + `financetoolkit` (Piotroski, ratios). No API key. Covers stocks/ETFs/FX/commodities/crypto via Yahoo symbology.
- **Sentiment**: stdlib `urllib.request` to CNN's public JSON endpoint. No deps, no scraping.
- **Composite proxies**: documented formulas in `app/composite_scores.py` reproducing Traderfox-style aggregates from public-methodology inputs.

Traderfox-specific code (`handle_playwright.py`, `dom.json`, Playwright dep, traderfox dispatch) is **removed** — not deprecated, not run alongside. `make run` becomes a no-op stub between PR 1B (decommission) and PR 1D (fundamentals); acceptable for a single-developer DRAFT/WIP repo.

## Consequences

**Won:**

- Auditable scoring (formulas in source code)
- Broader asset coverage (any Yahoo symbol)
- Lighter CI (no browser launches; ~5x runtime drop)
- No DOM-selector rot
- Aligns with no-API-keys repo theme

**Lost:**

- Traderfox's exact proprietary score values — composite proxies will track the underlying signal but won't equal Traderfox numbers byte-for-byte
- AAQS's German-investor weighting specificity — replaced by a generic Quality + low-volatility composite
- Direct UI parity with Traderfox's tab structure (irrelevant for a JSON-output CLI)

**Accepted risks:**

- `yfinance` is unofficial Yahoo scraping — rate-limit risk, occasional schema drift. Same trust class as the Playwright scraper it replaces.
- `financetoolkit` may want a Free FMP key for some endpoints. Free tier and yfinance-only fallback both work.
- `make run` non-functional during the PR-1B-to-PR-1D window. Mitigated by sequential merging; never lasts >1 session.

## Alternatives considered

- **Run alongside (Phase A→D over weeks).** Rejected: doubles maintenance surface during transition; Traderfox is fragile enough that "alongside" likely means "the old one breaks first".
- **Wrap Traderfox via `polyfetch-scrape` + Patchright.** Rejected: still depends on a single proprietary provider with unaudited scoring.
- **Paid data feeds (Bloomberg, Refinitiv, Tiingo, FMP premium).** Rejected: violates no-API-keys repo theme; each adds a recurring cost barrier for users.
- **OpenBB Platform.** Considered. Heavier than `yfinance`+`financetoolkit`; some endpoints require API keys. Revisit only if `financetoolkit` proves insufficient.

## References

- [`UserStory.md`](../UserStory.md), [`architecture.md`](../architecture.md), [`roadmap.md`](../roadmap.md)
- [yfinance](https://pypi.org/project/yfinance/), [financetoolkit](https://pypi.org/project/financetoolkit/)
- CNN F&G endpoint research: [#27 (closed, superseded by #17)](https://github.com/qte77/scrape-stock-kpi/issues/17)
