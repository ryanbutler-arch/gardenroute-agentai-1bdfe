"""Orchestrator — coordinates data collection and all agents for one ticker."""
from __future__ import annotations

import time
from typing import Any, Callable

from rich.console import Console

from scanner.data.market_data import MarketData
from scanner.data.news_data import fetch_all_news
from scanner.analysis import technical as tech_analysis
from scanner.analysis import fundamental as fund_analysis
from scanner.agents import bull_agent, bear_agent, challenge_agent, synthesis_agent
from scanner.config import config

console = Console()


def _step(label: str, fn: Callable, *args, **kwargs) -> Any:
    """Run a step with a spinner and return the result."""
    with console.status(f"[cyan]{label}...[/cyan]"):
        try:
            result = fn(*args, **kwargs)
            console.print(f"  [green]✓[/green] {label}")
            return result
        except Exception as e:
            console.print(f"  [red]✗[/red] {label} — {e}")
            return {}


def analyze_ticker(ticker: str, verbose: bool = False) -> dict[str, Any]:
    """
    Full analysis pipeline for a single ticker.
    Returns a complete result dict including the synthesis verdict.
    """
    ticker = ticker.upper().strip()
    console.rule(f"[bold blue]Analyzing {ticker}[/bold blue]")

    # ------------------------------------------------------------------
    # Phase 1: Data Collection
    # ------------------------------------------------------------------
    console.print("\n[bold]Phase 1: Data Collection[/bold]")
    md = MarketData(ticker)

    fundamentals = _step("Fetching fundamentals", md.fundamentals)
    price_history = _step("Fetching price history (5yr)", md.price_history, "5y")
    options = _step("Fetching options data", md.options_data)
    insider_tx = _step("Fetching insider transactions", md.insider_transactions)
    analyst_recs = _step("Fetching analyst recommendations", md.analyst_recommendations)
    earnings = _step("Fetching earnings history", md.earnings_history)
    news = _step("Fetching news & SEC filings", fetch_all_news, ticker)

    # ------------------------------------------------------------------
    # Phase 2: Quantitative Analysis
    # ------------------------------------------------------------------
    console.print("\n[bold]Phase 2: Quantitative Analysis[/bold]")
    technical = _step("Running technical analysis", tech_analysis.run, price_history)
    fundamental_scored = _step("Running fundamental scoring", fund_analysis.run, fundamentals)

    # ------------------------------------------------------------------
    # Package everything for agents
    # ------------------------------------------------------------------
    data_package = {
        "ticker": ticker,
        "fundamentals": fundamentals,
        "technical": technical,
        "fundamental_analysis": fundamental_scored,
        "options": options,
        "insider_transactions": insider_tx[:10],  # top 10
        "analyst_recommendations": analyst_recs,
        "earnings_history": earnings,
        "news": {
            "yahoo_finance_headlines": [
                a.get("title", "") for a in news.get("yahoo_finance", [])[:10]
            ],
            "sec_filings_count": news.get("total_filings", 0),
        },
    }

    # ------------------------------------------------------------------
    # Phase 3: Multi-Agent Analysis
    # ------------------------------------------------------------------
    console.print("\n[bold]Phase 3: Multi-Agent Analysis[/bold]")

    bull = _step("Bull Agent — building long case", bull_agent.analyze, ticker, data_package)
    bear = _step("Bear Agent — building short case", bear_agent.analyze, ticker, data_package)

    # ------------------------------------------------------------------
    # Phase 4: Adversarial Challenge
    # ------------------------------------------------------------------
    console.print("\n[bold]Phase 4: Adversarial Challenge[/bold]")
    challenge = _step(
        "Challenge Agent — probing both cases",
        challenge_agent.challenge,
        ticker, bull, bear, data_package,
    )

    # ------------------------------------------------------------------
    # Phase 5: Synthesis
    # ------------------------------------------------------------------
    console.print("\n[bold]Phase 5: Synthesis & Final Verdict[/bold]")
    verdict = _step(
        "Synthesis Agent — final verdict",
        synthesis_agent.synthesize,
        ticker, data_package, bull, bear, challenge,
    )

    return {
        "ticker": ticker,
        "fundamentals": fundamentals,
        "technical": technical,
        "fundamental_analysis": fundamental_scored,
        "options": options,
        "bull_case": bull,
        "bear_case": bear,
        "challenge_report": challenge,
        "verdict": verdict,
    }
