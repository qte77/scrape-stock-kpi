"""scrape-stock-kpi entrypoint.

Resolves the active asset universe from CLI args + reports its size.
Fundamentals fetching lands in #16; this stub validates that the
CliArgs → universe resolver chain works end-to-end.
"""

from rich.console import Console

from .universe import resolve_universe
from .utils.parse_args import CliArgs


def main() -> None:
    """Stub entrypoint until #16 lands."""
    console = Console()
    args = CliArgs()
    tickers = resolve_universe(args)
    console.print(
        f"[green]scrape-stock-kpi[/green] resolved "
        f"[bold]{len(tickers)}[/bold] tickers"
    )
    console.print(f"first 5: {tickers[:5]}")
    console.print(
        "[yellow]Fundamentals module pending — see issue #16.[/yellow]"
    )


if __name__ == "__main__":
    main()
