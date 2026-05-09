"""App-mode enum.

The Traderfox provider dispatch and score-aggregation helpers that previously
lived here were removed when the Traderfox scraper was decommissioned. See
``docs/decisions/0000-remove-traderfox.md`` and issue #19. The library-based
fundamentals replacement is tracked in #16.
"""

from enum import Enum


class AppModes(Enum):
    """Modes the app can run in (selects the asset CSV variant)."""

    DEFAULT = "prod"
    TEST = "test"
