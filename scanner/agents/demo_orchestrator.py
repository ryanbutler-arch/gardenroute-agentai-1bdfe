"""Demo orchestrator — uses mock data instead of live market feeds."""
from __future__ import annotations

from typing import Any, Callable

from rich.console import Console

from scanner.data.mock_data import (
    mock_price_history,
    mock_fundamentals,
    mock_options,
    mock_insider_transactions,
    mock_analyst_recs,
    mock_earnings,
    mock_news,
)
from scanner.analysis import technical as tech_analysis
from scanner.analysis import fundamental as fund_analysis
from scanner.agents import bull_agent, bear_agent, challenge_agent, synthesis_agent, research_agent
from scanner.data.mock_data import mock_research

console = Console()


def _step(label: str, fn: Callable, *args, **kwargs) -> Any:
    with console.status(f"[cyan]{label}...[/cyan]"):
        try:
            result = fn(*args, **kwargs)
            console.print(f"  [green]✓[/green] {label}")
            return result
        except Exception as e:
            console.print(f"  [red]✗[/red] {label} — {e}")
            return {}


def analyze_demo(ticker: str = "DEMO") -> dict[str, Any]:
    """Full pipeline using mock market data. Claude agents are still called live."""
    ticker = ticker.upper().strip()
    console.rule(f"[bold blue]Demo Analysis — {ticker}[/bold blue]")
    console.print("[yellow]Demo mode: using synthetic market data. Claude agents run live.[/yellow]\n")

    console.print("\n[bold]Phase 1: Data Collection (Mock)[/bold]")
    fundamentals = mock_fundamentals(ticker)
    console.print("  [green]✓[/green] Fundamentals (mock)")
    price_history = mock_price_history(ticker)
    console.print("  [green]✓[/green] Price history (synthetic 5yr)")
    options = mock_options()
    console.print("  [green]✓[/green] Options data (mock)")
    insider_tx = mock_insider_transactions()
    console.print("  [green]✓[/green] Insider transactions (mock)")
    analyst_recs = mock_analyst_recs()
    console.print("  [green]✓[/green] Analyst recommendations (mock)")
    earnings = mock_earnings()
    console.print("  [green]✓[/green] Earnings history (mock)")
    news = mock_news(ticker)
    console.print("  [green]✓[/green] News & filings (mock)")

    console.print("\n[bold]Phase 2: Quantitative Analysis[/bold]")
    technical = _step("Running technical analysis", tech_analysis.run, price_history)
    fundamental_scored = _step("Running fundamental scoring", fund_analysis.run, fundamentals)

    console.print("\n[bold]Phase 2.5: Deep Web Research (Mock)[/bold]")
    raw_research = mock_research(ticker)
    console.print("  [green]✓[/green] Web research (mock — Finviz, DuckDuckGo, MarketWatch)")
    research_brief = _step(
        "Research Agent — verifying & synthesizing findings",
        research_agent.analyze,
        ticker, raw_research, fundamentals,
    )

    data_package = {
        "ticker": ticker,
        "fundamentals": fundamentals,
        "technical": technical,
        "fundamental_analysis": fundamental_scored,
        "options": options,
        "insider_transactions": insider_tx,
        "analyst_recommendations": analyst_recs,
        "earnings_history": earnings,
        "news": {
            "yahoo_finance_headlines": news["yahoo_finance_headlines"],
            "sec_filings_count": news["sec_filings_count"],
        },
        "deep_research": research_brief,
    }

    console.print("\n[bold]Phase 3: Multi-Agent Analysis[/bold]")
    bull = _step("Bull Agent — building long case", bull_agent.analyze, ticker, data_package)
    bear = _step("Bear Agent — building short case", bear_agent.analyze, ticker, data_package)

    console.print("\n[bold]Phase 4: Adversarial Challenge[/bold]")
    challenge = _step(
        "Challenge Agent — probing both cases",
        challenge_agent.challenge,
        ticker, bull, bear, data_package,
    )

    console.print("\n[bold]Phase 5: Synthesis & Final Verdict[/bold]")
    verdict = _step(
        "Synthesis Agent — final verdict",
        synthesis_agent.synthesize,
        ticker, data_package, bull, bear, challenge,
    )

    return {
        "ticker": ticker,
        "mode": "demo",
        "fundamentals": fundamentals,
        "technical": technical,
        "fundamental_analysis": fundamental_scored,
        "options": options,
        "research_brief": research_brief,
        "bull_case": bull,
        "bear_case": bear,
        "challenge_report": challenge,
        "verdict": verdict,
    }
