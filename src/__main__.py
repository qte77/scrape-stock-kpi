"""analyze-stock-kpi entrypoint.

Resolves the active asset universe, prints a CNN Fear & Greed sentiment
banner, fetches fundamentals via yfinance, prints an equities/ETF summary
table, and persists every snapshot (including sparse ones for
FX/futures/crypto) to ``results/fundamentals_<UTC>.json``.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .composite_scores import CompositeScores, compute_scores
from .fundamentals import FundamentalsSnapshot, fetch_universe_fundamentals
from .sentiment import FearGreedSnapshot, fetch_fear_greed
from .universe import resolve_universe
from .utils.parse_args import CliArgs

RESULTS_DIR = Path("results")
_TABLE_QUOTE_TYPES = {"EQUITY", "ETF"}

logger = logging.getLogger(__name__)


def _format_market_cap(value: float | None) -> str:
    if value is None:
        return "-"
    if value >= 1e12:
        return f"{value / 1e12:.2f}T"
    if value >= 1e9:
        return f"{value / 1e9:.2f}B"
    if value >= 1e6:
        return f"{value / 1e6:.2f}M"
    return f"{value:,.0f}"


def _format_ratio(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "-"


def _format_percent(value: float | None) -> str:
    return f"{value * 100:.2f}%" if value is not None else "-"


def _format_score(value: float | None) -> str:
    return f"{value:.0f}" if value is not None else "-"


def _print_sentiment_banner(console: Console, snapshot: FearGreedSnapshot) -> None:
    stamp = snapshot.timestamp.strftime("%Y-%m-%d %H:%M %Z").strip()
    console.print(
        f"[bold]Fear & Greed[/bold] "
        f"[cyan]{snapshot.score:.1f}[/cyan] "
        f"([italic]{snapshot.rating}[/italic]) as of {stamp}"
    )


def _score_columns(snap: FundamentalsSnapshot) -> list[str]:
    scores = snap.composite_scores or CompositeScores()
    return [
        _format_score(scores.quality),
        _format_score(scores.dividend),
        _format_score(scores.growth),
    ]


def _summary_row(snap: FundamentalsSnapshot, show_scores: bool) -> list[str]:
    row = [
        snap.symbol,
        snap.sector or "-",
        _format_market_cap(snap.market_cap),
        _format_ratio(snap.trailing_pe),
        _format_percent(snap.return_on_equity),
        _format_percent(snap.dividend_yield),
    ]
    if show_scores:
        row += _score_columns(snap)
    return row


def _print_summary_table(
    console: Console,
    snapshots: list[FundamentalsSnapshot],
    *,
    show_scores: bool = False,
) -> None:
    table = Table(title="Fundamentals (equities & ETFs)")
    table.add_column("Symbol", style="bold")
    table.add_column("Sector")
    table.add_column("Market Cap", justify="right")
    table.add_column("P/E", justify="right")
    table.add_column("ROE", justify="right")
    table.add_column("Div Yield", justify="right")
    if show_scores:
        table.add_column("Quality", justify="right")
        table.add_column("Div", justify="right")
        table.add_column("Growth", justify="right")

    for snap in snapshots:
        if snap.quote_type not in _TABLE_QUOTE_TYPES:
            continue
        table.add_row(*_summary_row(snap, show_scores))
    console.print(table)


def _persist_snapshots(snapshots: list[FundamentalsSnapshot]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_path = RESULTS_DIR / f"fundamentals_{stamp}.json"
    payload = [s.model_dump(by_alias=False) for s in snapshots]
    out_path.write_text(json.dumps(payload, indent=2))
    return out_path


def main() -> None:
    console = Console()
    args = CliArgs()
    try:
        _print_sentiment_banner(console, fetch_fear_greed())
    except Exception as exc:
        logger.warning("Failed to fetch CNN Fear & Greed: %s", exc)
    tickers = resolve_universe(args)
    console.print(
        f"[green]analyze-stock-kpi[/green] resolving "
        f"[bold]{len(tickers)}[/bold] tickers"
    )
    raw_snapshots = fetch_universe_fundamentals(tickers)
    snapshots = [
        snap.model_copy(update={"composite_scores": compute_scores(snap)})
        for snap in raw_snapshots
    ]
    _print_summary_table(console, snapshots, show_scores=args.show_scores)
    out_path = _persist_snapshots(snapshots)
    console.print(f"[green]Wrote[/green] {out_path}")


if __name__ == "__main__":
    main()
