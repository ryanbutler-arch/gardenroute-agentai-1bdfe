#!/usr/bin/env python3
"""
Equities Scanner — CLI entry point.

Usage:
    python main.py AAPL
    python main.py AAPL MSFT NVDA          # scan multiple tickers
    python main.py AAPL --json             # output raw JSON
    python main.py --watchlist tech        # built-in watchlists
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime

from rich.console import Console

# Validate env before importing heavy modules
from scanner.config import config

console = Console()

WATCHLISTS = {
    "tech": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA"],
    "finance": ["JPM", "BAC", "GS", "MS", "BRK-B", "V", "MA"],
    "energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PXD"],
    "healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK", "LLY"],
    "consumer": ["PG", "KO", "PEP", "WMT", "COST", "TGT"],
    "indices": ["SPY", "QQQ", "DIA", "IWM", "GLD", "TLT"],
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-agent equities scanner with adversarial challenge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py AAPL
  python main.py AAPL MSFT NVDA
  python main.py --watchlist tech
  python main.py AAPL --json > aapl_report.json

Watchlists: """ + ", ".join(WATCHLISTS.keys()),
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Ticker symbol(s) to analyze (e.g. AAPL MSFT)",
    )
    parser.add_argument(
        "--watchlist", "-w",
        choices=list(WATCHLISTS.keys()),
        help="Scan a built-in watchlist",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON instead of formatted report",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Save JSON output to a file",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with synthetic mock data (no live market feed needed)",
    )

    args = parser.parse_args()

    # Resolve ticker list
    tickers: list[str] = []
    if args.watchlist:
        tickers = WATCHLISTS[args.watchlist]
    if args.tickers:
        tickers += [t.upper() for t in args.tickers]

    if not tickers:
        parser.print_help()
        console.print("\n[red]Error: provide at least one ticker or --watchlist[/red]")
        sys.exit(1)

    # Validate API key
    try:
        config.validate()
    except EnvironmentError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    # Lazy imports after validation
    from scanner.agents.orchestrator import analyze_ticker
    from scanner.agents.demo_orchestrator import analyze_demo
    from scanner.report.formatter import print_report

    results = []
    start_time = time.time()

    for ticker in tickers:
        try:
            result = analyze_demo(ticker) if args.demo else analyze_ticker(ticker)
            results.append(result)

            if not args.json:
                print_report(result)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error analyzing {ticker}: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    elapsed = time.time() - start_time

    # Summary table if multiple tickers
    if len(results) > 1 and not args.json:
        from rich.table import Table
        from rich import box as rbox

        summary = Table(
            title=f"SCAN SUMMARY — {len(results)} tickers in {elapsed:.0f}s",
            box=rbox.ROUNDED,
        )
        summary.add_column("Ticker", style="bold")
        summary.add_column("Company")
        summary.add_column("ST Verdict", justify="center")
        summary.add_column("LT Verdict", justify="center")
        summary.add_column("Conviction")
        summary.add_column("Fund Score")

        for r in results:
            v = r.get("verdict", {})
            st_v = v.get("short_term", {}).get("verdict", "?")
            lt_v = v.get("long_term", {}).get("verdict", "?")
            conv = v.get("overall_conviction", 0)
            fscore = r.get("fundamental_analysis", {}).get("overall_score", 0)
            name = r.get("fundamentals", {}).get("name", r["ticker"])[:30]
            summary.add_row(
                r["ticker"],
                name,
                st_v,
                lt_v,
                f"{conv}/100",
                f"{fscore}/100",
            )

        console.print(summary)

    # JSON output
    if args.json or args.output:
        output_data = json.dumps(results if len(results) > 1 else results[0], indent=2, default=str)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_data)
            console.print(f"[green]Results saved to {args.output}[/green]")
        elif args.json:
            print(output_data)

    console.print(f"\n[dim]Completed in {elapsed:.1f}s[/dim]")


if __name__ == "__main__":
    main()
