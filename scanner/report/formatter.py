"""Rich terminal report formatter."""
from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def _verdict_color(verdict: str) -> str:
    v = verdict.lower()
    if "strong buy" in v:
        return "bold green"
    elif "buy" in v:
        return "green"
    elif "strong sell" in v:
        return "bold red"
    elif "sell" in v:
        return "red"
    elif "avoid" in v:
        return "dark_orange"
    return "yellow"


def _conviction_bar(conviction: int) -> str:
    filled = round(conviction / 5)
    bar = "█" * filled + "░" * (20 - filled)
    color = "green" if conviction >= 70 else ("yellow" if conviction >= 50 else "red")
    return f"[{color}]{bar}[/{color}] {conviction}/100"


def _fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        color = "green" if v > 0 else ("red" if v < 0 else "white")
        return f"[{color}]{v:+.2f}%[/{color}]"
    except Exception:
        return str(val)


def _fmt_num(val, decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):,.{decimals}f}"
    except Exception:
        return str(val)


def _fmt_large(val) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if abs(v) >= 1e12:
            return f"${v/1e12:.2f}T"
        elif abs(v) >= 1e9:
            return f"${v/1e9:.2f}B"
        elif abs(v) >= 1e6:
            return f"${v/1e6:.2f}M"
        return f"${v:,.0f}"
    except Exception:
        return str(val)


def print_report(result: dict[str, Any]) -> None:
    ticker = result.get("ticker", "?")
    fundamentals = result.get("fundamentals", {})
    technical = result.get("technical", {})
    fund_analysis = result.get("fundamental_analysis", {})
    bull = result.get("bull_case", {})
    bear = result.get("bear_case", {})
    challenge = result.get("challenge_report", {})
    verdict = result.get("verdict", {})
    options = result.get("options", {})

    name = fundamentals.get("name", ticker)
    sector = fundamentals.get("sector", "N/A")
    price = fundamentals.get("current_price")
    currency = fundamentals.get("currency", "USD")

    console.print()
    console.rule(f"[bold white]EQUITIES SCANNER REPORT — {ticker}[/bold white]")

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    header = Table.grid(expand=True)
    header.add_column(ratio=2)
    header.add_column(ratio=1)
    header.add_row(
        f"[bold white]{name}[/bold white]\n"
        f"[dim]{sector} · {fundamentals.get('industry', 'N/A')} · {fundamentals.get('country', 'N/A')}[/dim]",
        f"[bold]{currency} {_fmt_num(price, 4)}[/bold]\n"
        f"[dim]Mkt Cap: {_fmt_large(fundamentals.get('market_cap'))}[/dim]",
    )
    console.print(Panel(header, title="Company Overview", border_style="blue"))

    # ------------------------------------------------------------------
    # Verdicts
    # ------------------------------------------------------------------
    st = verdict.get("short_term", {})
    lt = verdict.get("long_term", {})

    verdict_table = Table(box=box.ROUNDED, expand=True)
    verdict_table.add_column("Horizon", style="bold")
    verdict_table.add_column("Verdict", justify="center")
    verdict_table.add_column("Conviction")
    verdict_table.add_column("Rationale")

    for horizon, case in [("Short Term (1-3M)", st), ("Long Term (1-3Y)", lt)]:
        v_str = case.get("verdict", "Watch")
        verdict_table.add_row(
            horizon,
            f"[{_verdict_color(v_str)}]{v_str}[/{_verdict_color(v_str)}]",
            _conviction_bar(case.get("conviction", 0)),
            case.get("rationale", "")[:120] + "...",
        )

    console.print(Panel(
        verdict_table,
        title=f"[bold]FINAL VERDICT  ·  Overall Conviction: {_conviction_bar(verdict.get('overall_conviction', 0))}[/bold]",
        border_style="bold green" if verdict.get("overall_conviction", 0) >= 70 else "bold yellow",
    ))

    # ------------------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------------------
    console.print(Panel(
        verdict.get("final_summary", "No summary available."),
        title="[bold]Executive Summary[/bold]",
        border_style="white",
    ))

    # ------------------------------------------------------------------
    # Technical Snapshot
    # ------------------------------------------------------------------
    tech_table = Table(box=box.SIMPLE, expand=True)
    tech_table.add_column("Indicator", style="dim")
    tech_table.add_column("Value")
    tech_table.add_column("Indicator", style="dim")
    tech_table.add_column("Value")

    ma = technical.get("moving_averages", {})
    mom = technical.get("momentum", {})
    vol = technical.get("volatility", {})
    perf = technical.get("price_performance", {})

    tech_table.add_row("Trend", f"[bold]{technical.get('trend', 'N/A')}[/bold]",
                       "RSI(14)", f"{_fmt_num(mom.get('rsi_14'), 1)} [{mom.get('rsi_signal', 'N/A')}]")
    tech_table.add_row("Cross Signal", str(technical.get("cross_signal") or "none"),
                       "MACD", f"{mom.get('macd_crossover', 'N/A')}")
    tech_table.add_row("vs SMA50", _fmt_pct(ma.get("price_vs_sma50_pct")),
                       "vs SMA200", _fmt_pct(ma.get("price_vs_sma200_pct")))
    tech_table.add_row("1M Return", _fmt_pct(perf.get("1m_pct")),
                       "1Y Return", _fmt_pct(perf.get("1y_pct")))
    tech_table.add_row("3M Return", _fmt_pct(perf.get("3m_pct")),
                       "Vol 30D (ann.)", f"{_fmt_num(vol.get('historical_vol_30d_annualized'), 1)}%")
    tech_table.add_row("BB Position", f"{_fmt_num(vol.get('bb_position_pct'), 1)}% [{vol.get('bb_signal', 'N/A')}]",
                       "OBV Trend", str(technical.get("volume", {}).get("obv_trend", "N/A")))

    if options.get("available"):
        tech_table.add_row("P/C Ratio", f"{options.get('put_call_ratio', 'N/A')} [{options.get('sentiment', '')}]",
                           "Options Exp.", str(options.get("expiration", "N/A")))

    console.print(Panel(tech_table, title="[bold]Technical Analysis[/bold]", border_style="cyan"))

    # ------------------------------------------------------------------
    # Fundamental Snapshot
    # ------------------------------------------------------------------
    fund_table = Table(box=box.SIMPLE, expand=True)
    fund_table.add_column("Metric", style="dim")
    fund_table.add_column("Value")
    fund_table.add_column("Metric", style="dim")
    fund_table.add_column("Value")

    f = fundamentals
    fa = fund_analysis.get("valuation", {})
    fp = fund_analysis.get("profitability", {})
    fg = fund_analysis.get("growth", {})
    fh = fund_analysis.get("health", {})

    fund_table.add_row("P/E (fwd)", _fmt_num(f.get("pe_forward"), 1),
                       "P/E (trail)", _fmt_num(f.get("pe_trailing"), 1))
    fund_table.add_row("PEG", _fmt_num(fa.get("peg"), 2),
                       "P/B", _fmt_num(fa.get("pb"), 2))
    fund_table.add_row("EV/EBITDA", _fmt_num(fa.get("ev_ebitda"), 1),
                       "Analyst Upside", _fmt_pct(fa.get("analyst_upside_pct")))
    fund_table.add_row("Gross Margin", _fmt_pct(fp.get("gross_margin_pct")),
                       "Operating Margin", _fmt_pct(fp.get("operating_margin_pct")))
    fund_table.add_row("Net Margin", _fmt_pct(fp.get("net_margin_pct")),
                       "ROE", _fmt_pct(fp.get("roe_pct")))
    fund_table.add_row("Rev Growth", _fmt_pct(fg.get("revenue_growth_pct")),
                       "EPS Growth", _fmt_pct(fg.get("earnings_growth_pct")))
    fund_table.add_row("Debt/Equity", _fmt_num(fh.get("debt_to_equity"), 2),
                       "Current Ratio", _fmt_num(fh.get("current_ratio"), 2))
    fund_table.add_row("Free CF", _fmt_large(fh.get("free_cashflow")),
                       "Total Cash", _fmt_large(fh.get("total_cash")))
    fund_table.add_row(
        "Beta", _fmt_num(f.get("beta"), 2),
        "Short Float", f"{_fmt_num(fund_analysis.get('sentiment_indicators', {}).get('short_percent_float'), 1)}%",
    )

    score = fund_analysis.get("overall_score", 0)
    score_color = "green" if score >= 65 else ("yellow" if score >= 45 else "red")
    console.print(Panel(
        fund_table,
        title=f"[bold]Fundamental Analysis  ·  Score: [{score_color}]{score}/100[/{score_color}][/bold]",
        border_style="magenta",
    ))

    # ------------------------------------------------------------------
    # Fundamental Flags
    # ------------------------------------------------------------------
    flags = fund_analysis.get("flags", [])
    if flags:
        flags_text = "\n".join(f"  • {f}" for f in flags)
        console.print(Panel(flags_text, title="[bold]Fundamental Flags[/bold]", border_style="dim"))

    # ------------------------------------------------------------------
    # Bull vs Bear
    # ------------------------------------------------------------------
    bb_table = Table(box=box.ROUNDED, expand=True, show_lines=True)
    bb_table.add_column("BULL CASE", style="green", ratio=1)
    bb_table.add_column("BEAR CASE", style="red", ratio=1)

    bull_pts = bull.get("key_catalysts", []) + bull.get("fundamental_positives", [])
    bear_pts = bear.get("key_risks", []) + bear.get("fundamental_negatives", [])
    max_rows = max(len(bull_pts), len(bear_pts), 3)

    for i in range(min(max_rows, 8)):
        b_pt = bull_pts[i] if i < len(bull_pts) else ""
        s_pt = bear_pts[i] if i < len(bear_pts) else ""
        bb_table.add_row(str(b_pt)[:100], str(s_pt)[:100])

    bb_conv = Table.grid(expand=True)
    bb_conv.add_column(ratio=1)
    bb_conv.add_column(ratio=1)
    bb_conv.add_row(
        f"[green]Bull conviction:[/green] {_conviction_bar(bull.get('conviction', 0))}",
        f"[red]Bear conviction:[/red] {_conviction_bar(bear.get('conviction', 0))}",
    )

    console.print(Panel(bb_table, title="[bold]Bull vs Bear Arguments[/bold]", border_style="white"))
    console.print(bb_conv)

    # ------------------------------------------------------------------
    # Challenge Report
    # ------------------------------------------------------------------
    stronger = challenge.get("stronger_case", "tie")
    stronger_color = "green" if stronger == "bull" else ("red" if stronger == "bear" else "yellow")

    challenge_text = (
        f"[{stronger_color}]Stronger case after challenge: {stronger.upper()}[/{stronger_color}]\n\n"
        f"{challenge.get('challenge_summary', '')}\n\n"
    )
    if challenge.get("critical_uncertainties"):
        challenge_text += "[bold]Critical Uncertainties:[/bold]\n"
        challenge_text += "\n".join(f"  • {u}" for u in challenge["critical_uncertainties"])

    console.print(Panel(challenge_text, title="[bold]Adversarial Challenge Report[/bold]", border_style="yellow"))

    # ------------------------------------------------------------------
    # Action Guidance
    # ------------------------------------------------------------------
    invalidation = verdict.get("invalidation_conditions", [])
    watch_list = verdict.get("what_to_watch", [])
    pos_size = verdict.get("position_sizing", "none")
    stop_loss = verdict.get("stop_loss_suggestion", "N/A")

    console.print(Panel(
        f"[bold]Position Sizing:[/bold] {pos_size}\n"
        f"[bold]Stop Loss:[/bold] {stop_loss}\n\n"
        "[bold]Invalidation Conditions:[/bold]\n" + "\n".join(f"  • {c}" for c in invalidation[:4]) + "\n\n"
        "[bold]What to Watch:[/bold]\n" + "\n".join(f"  • {w}" for w in watch_list[:4]),
        title="[bold]Action Guidance[/bold]",
        border_style="blue",
    ))

    # ------------------------------------------------------------------
    # Confidence note
    # ------------------------------------------------------------------
    console.print(Panel(
        f"[dim]{verdict.get('confidence_note', '')}[/dim]",
        title="[dim]Confidence & Data Quality Note[/dim]",
        border_style="dim",
    ))

    console.rule("[dim]End of Report[/dim]")
