"""CLI args + env vars typed via pydantic-settings.

`CliArgs` is the single source of truth for all runtime configuration that
comes from outside the process. Instantiate with `CliArgs()` and
``cli_parse_args=True`` reads ``sys.argv`` automatically.

The legacy argparse-based ``parse_args()`` function returned a loose
``dict[str, str | bool]`` that callers had to index by string key. The
pydantic settings model gives every field its precise type at the boundary
and removes the type-narrowing burden from callers.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class CliArgs(BaseSettings):
    """Parsed CLI args (and matching env vars).

    The asset universe is selected by **exactly one** of these fields, in
    precedence order: ``tickers`` > ``tickers_file`` > ``universe``. The
    resolver in :mod:`src.universe` enforces the precedence at runtime.
    """

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_kebab_case=True,
        cli_implicit_flags=True,
        env_prefix="SSK_",
        case_sensitive=False,
        extra="forbid",
    )

    universe: str = "qte77-watchlist"
    """Preset universe name (file basename in `src/assets/universes/`)."""

    tickers: str | None = None
    """Comma-separated Yahoo symbols, e.g. ``MSFT,SPY,EURUSD=X,GC=F``."""

    tickers_file: Path | None = None
    """Path to a file containing one Yahoo symbol per line."""

    period: str = "5y"
    """Price-history depth for :func:`src.fundamentals.fetch_price_history`.

    Accepts any value yfinance accepts (``1d``/``5d``/``1mo``/``1y``/``5y``
    /``max`` etc.). Not consumed by the default fundamentals flow in
    :mod:`src.__main__`; reserved for the v0.5.0 composites PR (#18).
    """
