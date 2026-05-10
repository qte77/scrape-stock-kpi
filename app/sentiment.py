"""CNN Fear & Greed Index sentiment via stdlib HTTP.

Public API:
    - :func:`fetch_fear_greed` returns the headline :class:`FearGreedSnapshot`
      (used by the ``make run`` banner).
    - ``python -m app.sentiment`` fetches the full payload and merges the
      headline + ~1y historical points into per-year files at
      ``results/cnn_fg/YYYY.json`` — sorted-by-date JSON arrays. Today's
      entry is always overwritten with the live headline (which carries
      ``previous_*`` deltas); older dates are gap-filled and only updated
      if a fresher CNN timestamp arrives.

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


def _year_path(year: int, *, root: Path = RESULTS_DIR) -> Path:
    return root / f"{year}.json"


def _load_year(year: int, *, root: Path = RESULTS_DIR) -> dict[str, FearGreedSnapshot]:
    """Load the per-year file as a date-keyed dict, or empty if missing."""
    path = _year_path(year, root=root)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return {item["timestamp"][:10]: FearGreedSnapshot.model_validate(item) for item in raw}


def _write_year(
    year: int, by_date: dict[str, FearGreedSnapshot], *, root: Path = RESULTS_DIR
) -> Path:
    """Write a year's snapshots as a date-sorted JSON array."""
    root.mkdir(parents=True, exist_ok=True)
    path = _year_path(year, root=root)
    payload = [by_date[k].model_dump(mode="json") for k in sorted(by_date)]
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def _upsert(
    by_date: dict[str, FearGreedSnapshot], snap: FearGreedSnapshot, *, force: bool
) -> bool:
    """Insert/replace a snapshot keyed by its UTC date.

    ``force=True`` always wins (used for the live headline). Otherwise only
    inserts when missing or when the incoming timestamp is strictly newer
    than the stored one.
    """
    date_key = snap.timestamp.astimezone(UTC).strftime("%Y-%m-%d")
    existing = by_date.get(date_key)
    if force or existing is None or snap.timestamp > existing.timestamp:
        by_date[date_key] = snap
        return True
    return False


def merge_payload_into_years(
    payload: dict[str, Any], *, root: Path = RESULTS_DIR
) -> dict[int, dict[str, FearGreedSnapshot]]:
    """Apply a CNN payload onto the on-disk per-year history, in memory only.

    Returns the resulting ``{year: {date: snap}}`` mapping. The headline
    upsert is forced (today's reading always wins, including its
    ``previous_*`` fields). Historical entries fill gaps and refresh same-day
    duplicates that CNN has since updated.
    """
    headline = FearGreedSnapshot.model_validate(payload["fear_and_greed"])
    historical = parse_historical(payload)
    today_year = headline.timestamp.astimezone(UTC).year
    today_key = headline.timestamp.astimezone(UTC).strftime("%Y-%m-%d")

    by_year: dict[int, dict[str, FearGreedSnapshot]] = {}

    def _ensure(year: int) -> dict[str, FearGreedSnapshot]:
        if year not in by_year:
            by_year[year] = _load_year(year, root=root)
        return by_year[year]

    _upsert(_ensure(today_year), headline, force=True)
    for date_key, snap in historical.items():
        if date_key == today_key:
            continue
        _upsert(_ensure(snap.timestamp.astimezone(UTC).year), snap, force=False)
    return by_year


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    by_year = merge_payload_into_years(_fetch_payload())
    for year, by_date in by_year.items():
        path = _write_year(year, by_date)
        logger.info("Wrote %s with %d entries", path, len(by_date))


if __name__ == "__main__":
    main()
