"""scrape-stock-kpi entrypoint.

Parses CLI args via :class:`app.utils.parse_args.CliArgs` and reports them.
Universe resolution + fundamentals fetching land in subsequent PRs (#16, #20).
"""

from rich.console import Console

from .utils.parse_args import CliArgs


def main() -> None:
    """Stub entrypoint — echoes the parsed CliArgs until #16 lands."""
    console = Console()
    args = CliArgs()
    console.print(f"[yellow]scrape-stock-kpi[/yellow] received: {args.model_dump()}")
    console.print(
        "[yellow]Universe resolver and fundamentals module pending — "
        "see issues #20 and #16.[/yellow]"
    )


if __name__ == "__main__":
    main()
