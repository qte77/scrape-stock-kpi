"""CNN Fear & Greed Index sentiment via stdlib HTTP.

Public API:
    - :func:`fetch_fear_greed` returns the headline :class:`FearGreedSnapshot`
      (used by the ``make run`` banner).
    - ``python -m app.sentiment`` fetches the full payload and writes one
      date-keyed snapshot per CNN reading to ``results/cnn_fg/YYYY-MM-DD.json``.
      Today's file is rewritten each run (CNN updates intraday); historical
      files are immutable and skipped if they already exist.

CNN's WAF requires a browser-shape request — see ``USER_AGENT`` / ``ACCEPT``
/ ``REFERER`` constants. No external dependencies; stdlib ``urllib.request``
only.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

ENDPOINT = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
# CNN's WAF rejects unidentified clients with HTTP 418. The headers below
# mirror what edition.cnn.com itself sends when it XHRs the dataviz API:
# a current desktop-browser UA, an XHR-shape Accept, and a CNN Referer.
# All three are required when the egress IP is a datacenter range (e.g.
# GitHub Actions runners); from residential IPs the UA alone usually suffices.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)
ACCEPT = "application/json, text/plain, */*"
REFERER = "https://edition.cnn.com/"
REQUEST_TIMEOUT_SEC = 10
RESULTS_DIR = Path("results/cnn_fg")

logger = logging.getLogger(__name__)


class FearGreedSnapshot(BaseModel):
    """One CNN Fear & Greed reading.

    Used for both the live headline (with ``previous_*`` populated) and
    historical points (``previous_*`` are ``None`` because CNN's historical
    block doesn't carry them). Subindicators (VIX, breadth, momentum, etc.)
    are intentionally ignored — add modeled fields when a downstream consumer
    needs them.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    score: float
    rating: str
    timestamp: datetime
    previous_close: float | None = None
    previous_1_week: float | None = None
    previous_1_month: float | None = None
    previous_1_year: float | None = None


def _fetch_payload() -> dict[str, Any]:
    request = urllib.request.Request(
        ENDPOINT,
        headers={"User-Agent": USER_AGENT, "Accept": ACCEPT, "Referer": REFERER},
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SEC) as response:  # noqa: S310
        return json.loads(response.read())


def fetch_fear_greed() -> FearGreedSnapshot:
    """Fetch the current CNN Fear & Greed headline reading.

    Raises ``urllib.error.URLError`` on transport failure and
    ``pydantic.ValidationError`` on schema mismatch — callers decide whether
    to swallow or surface.
    """
    return FearGreedSnapshot.model_validate(_fetch_payload()["fear_and_greed"])


def parse_historical(payload: dict[str, Any]) -> dict[str, FearGreedSnapshot]:
    """Extract historical points from the CNN payload, deduped by UTC date.

    CNN ships multiple intraday entries per day; we keep the latest timestamp
    for each calendar date. Returns ``{ "YYYY-MM-DD": snapshot, ... }``.
    """
    historical = payload.get("fear_and_greed_historical", {}).get("data", [])
    by_date: dict[str, tuple[int, FearGreedSnapshot]] = {}
    for point in historical:
        ts_ms = int(point["x"])
        moment = datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
        date_key = moment.strftime("%Y-%m-%d")
        if date_key in by_date and ts_ms <= by_date[date_key][0]:
            continue
        by_date[date_key] = (
            ts_ms,
            FearGreedSnapshot(score=point["y"], rating=point["rating"], timestamp=moment),
        )
    return {date: snap for date, (_, snap) in by_date.items()}


def _persist_snapshot(snapshot: FearGreedSnapshot, *, overwrite: bool) -> Path | None:
    """Write one snapshot to ``results/cnn_fg/<date>.json``.

    Returns the path written, or ``None`` if the file already exists and
    ``overwrite`` is ``False`` (immutable historical entries).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_key = snapshot.timestamp.astimezone(UTC).strftime("%Y-%m-%d")
    out_path = RESULTS_DIR / f"{date_key}.json"
    if out_path.exists() and not overwrite:
        return None
    out_path.write_text(json.dumps(snapshot.model_dump(mode="json"), indent=2))
    return out_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    payload = _fetch_payload()
    headline = FearGreedSnapshot.model_validate(payload["fear_and_greed"])
    today_path = _persist_snapshot(headline, overwrite=True)
    logger.info(
        "Wrote %s (score=%.2f, rating=%s)", today_path, headline.score, headline.rating
    )
    historical = parse_historical(payload)
    today_date = headline.timestamp.astimezone(UTC).strftime("%Y-%m-%d")
    written = 0
    for date, snap in historical.items():
        if date == today_date:
            continue
        if _persist_snapshot(snap, overwrite=False) is not None:
            written += 1
    logger.info("Backfilled %d historical date(s)", written)


if __name__ == "__main__":
    main()
