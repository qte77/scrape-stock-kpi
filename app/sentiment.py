"""CNN Fear & Greed Index sentiment via stdlib HTTP.

Public API:
    - :func:`fetch_fear_greed` returns a :class:`FearGreedSnapshot`

The CNN endpoint requires a ``User-Agent`` header; without one it returns
HTTP 418. No external dependencies; stdlib ``urllib.request`` only.

Run ``python -m app.sentiment`` to fetch a snapshot and write it to
``results/fear_greed_<UTC>.json`` — this is what the daily GitHub Actions
cron invokes before committing the snapshot back to the repo.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

ENDPOINT = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
USER_AGENT = "Mozilla/5.0 (compatible; scrape-stock-kpi)"
REQUEST_TIMEOUT_SEC = 10
RESULTS_DIR = Path("results")

logger = logging.getLogger(__name__)


class FearGreedSnapshot(BaseModel):
    """Headline CNN Fear & Greed reading.

    Subindicators (VIX, breadth, momentum, etc.) are intentionally ignored
    in v0.4.0 — add modeled fields when a downstream consumer needs them.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    score: float
    rating: str
    timestamp: datetime
    previous_close: float | None = None
    previous_1_week: float | None = None
    previous_1_month: float | None = None
    previous_1_year: float | None = None


def fetch_fear_greed() -> FearGreedSnapshot:
    """Fetch the current CNN Fear & Greed snapshot.

    Raises ``urllib.error.URLError`` on transport failure and
    ``pydantic.ValidationError`` on schema mismatch — callers decide
    whether to swallow or surface.
    """
    request = urllib.request.Request(ENDPOINT, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SEC) as response:  # noqa: S310
        payload = json.loads(response.read())
    return FearGreedSnapshot.model_validate(payload["fear_and_greed"])


def _persist_snapshot(snapshot: FearGreedSnapshot) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_path = RESULTS_DIR / f"fear_greed_{stamp}.json"
    out_path.write_text(json.dumps(snapshot.model_dump(mode="json"), indent=2))
    return out_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    snapshot = fetch_fear_greed()
    out_path = _persist_snapshot(snapshot)
    logger.info(
        "Wrote %s (score=%.2f, rating=%s)", out_path, snapshot.score, snapshot.rating
    )


if __name__ == "__main__":
    main()
