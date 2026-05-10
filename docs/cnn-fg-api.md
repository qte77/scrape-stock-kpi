# CNN Fear & Greed API reference

Observed shape of `https://production.dataviz.cnn.io/index/fearandgreed/graphdata`,
captured live on 2026-05-10 via a one-shot inspector. CNN does not publish a
formal schema; this is the source of truth for what `app/sentiment.py` may rely
on.

## Top-level keys

```text
fear_and_greed              dict — the headline reading
fear_and_greed_historical   dict — ~1y of daily headline scores (data list)
market_momentum_sp500       dict — subindicator
market_momentum_sp125       dict — subindicator
stock_price_strength        dict — subindicator
stock_price_breadth         dict — subindicator
put_call_options            dict — subindicator
market_volatility_vix       dict — subindicator
market_volatility_vix_50    dict — subindicator (50-day VIX MA)
junk_bond_demand            dict — subindicator
safe_haven_demand           dict — subindicator
```

## `fear_and_greed` (the headline)

The only block that carries deltas relative to "today".

```json
{
  "score": 66.91,
  "rating": "greed",
  "timestamp": "2026-05-08T23:59:55+00:00",
  "previous_close": 67.57,
  "previous_1_week": 71.17,
  "previous_1_month": 29.17,
  "previous_1_year": 57.66
}
```

| Field | Type | Notes |
|---|---|---|
| `score` | `float` (0–100) | The composite F&G index |
| `rating` | `str` | One of `extreme fear`, `fear`, `neutral`, `greed`, `extreme greed` |
| `timestamp` | `str` (ISO 8601 with tz) | When the score was last recomputed |
| `previous_close` | `float` | Score at the previous market close |
| `previous_1_week` | `float` | Score 1 week ago |
| `previous_1_month` | `float` | Score 1 month ago |
| `previous_1_year` | `float` | Score 1 year ago |

## `fear_and_greed_historical`

Same shape as the subindicators below.

```json
{
  "timestamp": 1778284795000,
  "score": 66.91,
  "rating": "greed",
  "data": [
    {"x": 1747008000000, "y": 64.49, "rating": "greed"},
    {"x": 1747094400000, "y": 60.10, "rating": "greed"}
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `timestamp` | `float` (ms epoch) | Same as the headline `timestamp` field, ms instead of ISO |
| `score` | `float` (0–100) | Same as the headline `score` |
| `rating` | `str` | Same as the headline `rating` |
| `data` | `list[{x: float, y: float, rating: str}]` | ~250 daily points (~1 year). `x` is ms epoch UTC; `y` is the score; `rating` is the bucket. **No `previous_*` fields** — those exist only on the headline. |

## Subindicators (10 of them)

Every subindicator block has the **same** four-key shape as
`fear_and_greed_historical`:

```text
{
  timestamp: float (ms epoch)        — when this subindicator was last computed
  score:     float (0-100)           — the subindicator's contribution to F&G
  rating:    str                     — bucket name (same vocabulary as headline)
  data:      list[{x, y, rating}]    — ~250 daily points
}
```

The `data[i].y` value is **subindicator-specific** (NOT a 0–100 score). It is
the raw underlying measurement that drives that subindicator. Examples
captured 2026-05-08:

| Subindicator | Top-level `score` | `data[].y` represents |
|---|---|---|
| `market_momentum_sp500` | 99.6 | S&P 500 level (e.g. 5844.19) |
| `market_momentum_sp125` | 99.6 | S&P 500 125-day MA (e.g. 5819.98) |
| `stock_price_strength` | 61.4 | New-highs vs new-lows ratio (e.g. 0.257) |
| `stock_price_breadth` | 62.2 | NYSE McClellan volume summation (e.g. 1276.64) |
| `put_call_options` | 77.4 | Put/call ratio (e.g. 0.704) |
| `market_volatility_vix` | 50.0 | VIX level (e.g. 18.39) |
| `market_volatility_vix_50` | n/a | VIX 50-day MA |
| `junk_bond_demand` | 24.0 | High-yield vs investment-grade spread (e.g. 1.394) |
| `safe_haven_demand` | 93.6 | Stocks-vs-bonds 20-day return spread (e.g. 8.701) |

## What we model in `FearGreedSnapshot`

Only the headline's seven fields. Subindicators are accessible from
`_fetch_payload()` but not modeled — add fields when a downstream consumer
needs them.

For historical entries written to `results/cnn_fg/YYYY.json`, the
`previous_*` fields are `null` because CNN's `data` points don't carry them.
Only the **today** entry — written from the headline block — has populated
`previous_*` values, and only on the day the cron ran.

## How to refresh this doc

If CNN changes the shape, re-run the inspector against the live endpoint
from a residential IP or a one-shot CI workflow. Look for new top-level keys,
new fields inside the headline, or shape changes in `data[]` items — anything
new will silently drop through `extra="ignore"` until modeled.
