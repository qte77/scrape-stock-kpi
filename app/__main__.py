"""scrape-stock-kpi entrypoint.

The Traderfox scraper has been decommissioned (see
``docs/decisions/0000-remove-traderfox.md`` and issue #19). The library-based
fundamentals module is in progress; see issue #16.

Until #16 lands, ``python -m app`` echoes the parsed CLI args and exits.
"""

from rich.console import Console

from .utils.parse_args import parse_args


def main() -> None:
    """Stub entrypoint until #16 lands."""
    console = Console()
    args = parse_args()
    console.print(f"[yellow]scrape-stock-kpi[/yellow] received: {args}")
    console.print(
        "[yellow]Traderfox scraper decommissioned. "
        "Library-based fundamentals pending — see issue #16.[/yellow]"
    )


if __name__ == "__main__":
    main()
