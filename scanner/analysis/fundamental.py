"""Fundamental analysis — scoring and grading of financial health metrics."""
from __future__ import annotations

from typing import Any


def _grade(value, thresholds: list, labels: list, higher_better: bool = True) -> str:
    """Map a numeric value to a letter grade using thresholds."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"

    pairs = list(zip(thresholds, labels))
    if higher_better:
        for threshold, label in sorted(pairs, reverse=True):
            if v >= threshold:
                return label
    else:
        for threshold, label in sorted(pairs):
            if v <= threshold:
                return label
    return labels[-1]


def run(fundamentals: dict[str, Any]) -> dict[str, Any]:
    """Score and narrate fundamental metrics. Returns structured analysis."""
    f = fundamentals
    scores: list[int] = []   # 0-10 per metric
    flags: list[str] = []    # notable positives / negatives

    # ------------------------------------------------------------------
    # Valuation
    # ------------------------------------------------------------------
    pe = f.get("pe_forward") or f.get("pe_trailing")
    pe_grade = _grade(pe, [10, 15, 20, 30, 50], ["A+", "A", "B", "C", "D"], higher_better=False)
    if pe is not None:
        if pe < 15:
            scores.append(9); flags.append("Attractive P/E below 15")
        elif pe < 25:
            scores.append(6)
        elif pe < 40:
            scores.append(4); flags.append("Elevated P/E above 25")
        else:
            scores.append(2); flags.append("Very high P/E — growth must justify")

    peg = f.get("peg")
    if peg is not None:
        if peg < 1:
            scores.append(9); flags.append(f"PEG {peg:.2f} < 1 — potentially undervalued growth")
        elif peg < 2:
            scores.append(6)
        else:
            scores.append(3); flags.append(f"PEG {peg:.2f} elevated — growth may be priced in")

    pb = f.get("pb")
    if pb is not None:
        if pb < 1:
            scores.append(9); flags.append("Price < book value — deep value signal")
        elif pb < 3:
            scores.append(6)
        else:
            scores.append(4)

    ev_ebitda = f.get("ev_ebitda")
    if ev_ebitda is not None:
        if ev_ebitda < 8:
            scores.append(9); flags.append(f"EV/EBITDA {ev_ebitda:.1f} — cheap vs peers")
        elif ev_ebitda < 15:
            scores.append(6)
        else:
            scores.append(3); flags.append(f"EV/EBITDA {ev_ebitda:.1f} elevated")

    # Upside to analyst target
    price = f.get("current_price")
    target = f.get("target_mean_price")
    upside_pct = None
    if price and target and price > 0:
        upside_pct = round((target / price - 1) * 100, 1)
        if upside_pct > 30:
            scores.append(9); flags.append(f"Analyst consensus implies {upside_pct}% upside")
        elif upside_pct > 10:
            scores.append(7)
        elif upside_pct > 0:
            scores.append(5)
        else:
            scores.append(3); flags.append(f"Trading above analyst consensus target ({upside_pct}% downside)")

    # ------------------------------------------------------------------
    # Profitability
    # ------------------------------------------------------------------
    roe = f.get("roe")
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct > 20:
            scores.append(9); flags.append(f"Strong ROE {roe_pct:.1f}%")
        elif roe_pct > 12:
            scores.append(7)
        elif roe_pct > 0:
            scores.append(4)
        else:
            scores.append(1); flags.append("Negative ROE — loss-making")

    op_margin = f.get("operating_margin")
    if op_margin is not None:
        om_pct = op_margin * 100
        if om_pct > 25:
            scores.append(9); flags.append(f"Exceptional operating margin {om_pct:.1f}%")
        elif om_pct > 15:
            scores.append(7)
        elif om_pct > 5:
            scores.append(5)
        elif om_pct > 0:
            scores.append(3)
        else:
            scores.append(1); flags.append("Negative operating margin")

    # ------------------------------------------------------------------
    # Growth
    # ------------------------------------------------------------------
    rev_growth = f.get("revenue_growth")
    if rev_growth is not None:
        rg_pct = rev_growth * 100
        if rg_pct > 20:
            scores.append(9); flags.append(f"Revenue growing {rg_pct:.1f}% YoY — high growth")
        elif rg_pct > 10:
            scores.append(7)
        elif rg_pct > 0:
            scores.append(5)
        else:
            scores.append(2); flags.append(f"Revenue declining {rg_pct:.1f}% YoY")

    eps_growth = f.get("earnings_growth")
    if eps_growth is not None:
        eg_pct = eps_growth * 100
        if eg_pct > 25:
            scores.append(9); flags.append(f"EPS growing {eg_pct:.1f}% YoY")
        elif eg_pct > 10:
            scores.append(7)
        elif eg_pct > 0:
            scores.append(5)
        else:
            scores.append(2); flags.append(f"EPS declining {eg_pct:.1f}% YoY")

    # ------------------------------------------------------------------
    # Financial health
    # ------------------------------------------------------------------
    dte = f.get("debt_to_equity")
    if dte is not None:
        if dte < 0.3:
            scores.append(9); flags.append("Low debt — fortress balance sheet")
        elif dte < 1.0:
            scores.append(7)
        elif dte < 2.0:
            scores.append(4)
        else:
            scores.append(1); flags.append(f"High debt/equity {dte:.1f} — leverage risk")

    current_ratio = f.get("current_ratio")
    if current_ratio is not None:
        if current_ratio > 2:
            scores.append(9)
        elif current_ratio > 1.5:
            scores.append(7)
        elif current_ratio > 1:
            scores.append(5)
        else:
            scores.append(2); flags.append("Current ratio below 1 — liquidity concern")

    fcf = f.get("free_cashflow")
    if fcf is not None:
        if fcf > 0:
            scores.append(8); flags.append("Positive free cash flow")
        else:
            scores.append(2); flags.append("Negative free cash flow — cash burn")

    # ------------------------------------------------------------------
    # Short-selling / insider sentiment
    # ------------------------------------------------------------------
    short_pct = f.get("short_percent_float")
    if short_pct is not None:
        sp = short_pct * 100
        if sp > 20:
            scores.append(2); flags.append(f"High short interest {sp:.1f}% of float")
        elif sp > 10:
            scores.append(5)
        else:
            scores.append(8)

    insider_held = f.get("held_percent_insiders")
    if insider_held is not None:
        ip = insider_held * 100
        if ip > 20:
            scores.append(8); flags.append(f"Significant insider ownership {ip:.1f}%")
        elif ip > 5:
            scores.append(6)
        else:
            scores.append(4)

    # ------------------------------------------------------------------
    # Overall score
    # ------------------------------------------------------------------
    overall = round(sum(scores) / len(scores) * 10) if scores else 0  # 0-100

    return {
        "overall_score": overall,
        "flags": flags,
        "valuation": {
            "pe": pe,
            "pe_grade": pe_grade,
            "peg": peg,
            "pb": pb,
            "ev_ebitda": ev_ebitda,
            "analyst_upside_pct": upside_pct,
        },
        "profitability": {
            "roe_pct": round(f.get("roe", 0) * 100, 2) if f.get("roe") else None,
            "roa_pct": round(f.get("roa", 0) * 100, 2) if f.get("roa") else None,
            "gross_margin_pct": round(f.get("gross_margin", 0) * 100, 2) if f.get("gross_margin") else None,
            "operating_margin_pct": round(f.get("operating_margin", 0) * 100, 2) if f.get("operating_margin") else None,
            "net_margin_pct": round(f.get("profit_margin", 0) * 100, 2) if f.get("profit_margin") else None,
        },
        "growth": {
            "revenue_growth_pct": round(f.get("revenue_growth", 0) * 100, 2) if f.get("revenue_growth") else None,
            "earnings_growth_pct": round(f.get("earnings_growth", 0) * 100, 2) if f.get("earnings_growth") else None,
        },
        "health": {
            "debt_to_equity": dte,
            "current_ratio": current_ratio,
            "quick_ratio": f.get("quick_ratio"),
            "free_cashflow": fcf,
            "total_cash": f.get("total_cash"),
            "total_debt": f.get("total_debt"),
        },
        "sentiment_indicators": {
            "short_percent_float": round(short_pct * 100, 2) if short_pct else None,
            "short_ratio": f.get("short_ratio"),
            "insider_ownership_pct": round(insider_held * 100, 2) if insider_held else None,
            "institutional_ownership_pct": round(f.get("held_percent_institutions", 0) * 100, 2) if f.get("held_percent_institutions") else None,
        },
    }
