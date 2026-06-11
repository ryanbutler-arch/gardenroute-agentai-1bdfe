"""
Realistic mock data for testing / demo mode without live market feeds.
Data is representative of a large-cap tech stock (loosely AAPL-like).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Seed for reproducibility
_RNG = np.random.default_rng(42)


def mock_price_history(ticker: str = "DEMO") -> pd.DataFrame:
    """Generate 5 years of synthetic OHLCV data with realistic trend."""
    n = 252 * 5  # 5 trading years
    dates = pd.bdate_range(end="2026-05-28", periods=n)

    # Random walk with upward drift
    log_returns = _RNG.normal(0.0003, 0.012, n)
    prices = 150 * np.exp(np.cumsum(log_returns))

    df = pd.DataFrame(index=dates)
    df["Close"] = prices
    df["Open"] = prices * _RNG.uniform(0.99, 1.01, n)
    df["High"] = prices * _RNG.uniform(1.00, 1.025, n)
    df["Low"] = prices * _RNG.uniform(0.975, 1.00, n)
    df["Volume"] = _RNG.integers(50_000_000, 120_000_000, n).astype(float)
    df.index.name = "Date"
    return df


def mock_fundamentals(ticker: str = "DEMO") -> dict:
    return {
        "name": f"Demo Corp ({ticker})",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "country": "United States",
        "currency": "USD",
        "market_cap": 2_800_000_000_000,
        "enterprise_value": 2_760_000_000_000,
        "pe_trailing": 28.5,
        "pe_forward": 24.1,
        "peg": 1.8,
        "pb": 42.3,
        "ps_trailing": 7.2,
        "ev_ebitda": 19.4,
        "ev_revenue": 7.1,
        "gross_margin": 0.445,
        "operating_margin": 0.298,
        "profit_margin": 0.255,
        "roe": 1.471,
        "roa": 0.285,
        "revenue_growth": 0.042,
        "earnings_growth": 0.073,
        "earnings_quarterly_growth": 0.082,
        "current_ratio": 0.988,
        "quick_ratio": 0.916,
        "debt_to_equity": 1.52,
        "total_cash": 67_150_000_000,
        "total_debt": 104_590_000_000,
        "free_cashflow": 93_000_000_000,
        "operating_cashflow": 118_000_000_000,
        "dividend_yield": 0.0055,
        "payout_ratio": 0.153,
        "shares_outstanding": 15_200_000_000,
        "shares_short": 101_000_000,
        "short_ratio": 1.2,
        "short_percent_float": 0.0066,
        "held_percent_institutions": 0.608,
        "held_percent_insiders": 0.028,
        "current_price": 189.30,
        "52w_high": 237.23,
        "52w_low": 164.08,
        "target_mean_price": 222.50,
        "target_high_price": 275.00,
        "target_low_price": 165.00,
        "analyst_count": 38,
        "recommendation": "buy",
        "beta": 1.21,
        "description": (
            "Demo Corp designs, manufactures, and markets smartphones, personal computers, "
            "tablets, wearables, and accessories worldwide. The company also sells various "
            "related services including digital content, cloud storage, and enterprise solutions."
        ),
    }


def mock_options() -> dict:
    return {
        "available": True,
        "expiration": "2026-06-20",
        "calls_volume": 412_000,
        "puts_volume": 298_000,
        "put_call_ratio": 0.723,
        "sentiment": "bullish",
    }


def mock_insider_transactions() -> list:
    return [
        {"date": "2026-04-15", "insider": "Tim Apple (CEO)", "shares": -50000, "value": -9_450_000, "transaction": "Sale"},
        {"date": "2026-03-10", "insider": "CFO Demo", "shares": -20000, "value": -3_780_000, "transaction": "Sale"},
        {"date": "2026-02-01", "insider": "Director Smith", "shares": 10000, "value": 1_890_000, "transaction": "Purchase"},
    ]


def mock_analyst_recs() -> list:
    return [
        {"firm": "Goldman Sachs", "grade": "Buy", "action": "Reiterated"},
        {"firm": "Morgan Stanley", "grade": "Overweight", "action": "Reiterated"},
        {"firm": "Barclays", "grade": "Overweight", "action": "Upgrade"},
        {"firm": "JP Morgan", "grade": "Overweight", "action": "Reiterated"},
        {"firm": "UBS", "grade": "Neutral", "action": "Downgrade"},
        {"firm": "Bernstein", "grade": "Outperform", "action": "Initiated"},
    ]


def mock_earnings() -> list:
    return [
        {"date": "2026-04-30", "eps_estimate": 1.58, "eps_actual": 1.65, "surprise_pct": 4.4},
        {"date": "2026-01-29", "eps_estimate": 2.34, "eps_actual": 2.40, "surprise_pct": 2.6},
        {"date": "2025-10-30", "eps_estimate": 1.60, "eps_actual": 1.64, "surprise_pct": 2.5},
        {"date": "2025-07-30", "eps_estimate": 1.34, "eps_actual": 1.40, "surprise_pct": 4.5},
        {"date": "2025-04-24", "eps_estimate": 1.51, "eps_actual": 1.53, "surprise_pct": 1.3},
    ]


def mock_research(ticker: str) -> dict:
    """Simulated deep web research output (replaces live scraping in demo mode)."""
    return {
        "ticker": ticker,
        "sources_queried": ["finviz.com", "duckduckgo_news_search", "marketwatch.com"],
        "finviz": {
            "available": True,
            "market_cap": "2.80T",
            "pe": "28.50",
            "forward_pe": "24.10",
            "peg": "1.80",
            "eps_ttm": "6.64",
            "eps_next_year": "+8.21%",
            "sales_growth": "+4.20%",
            "eps_growth_qoq": "+7.30%",
            "insider_own": "2.80%",
            "short_float": "0.66%",
            "target_price": "222.50",
            "rsi": "45.81",
            "analyst_recom": "1.80",
            "52w_range": "164.08 - 237.23",
            "perf_week": "+1.20%",
            "perf_month": "+4.03%",
            "perf_ytd": "-3.20%",
            "perf_year": "+1.76%",
            "debt_eq": "1.52",
            "roe": "147.10%",
            "gross_margin": "44.50%",
            "oper_margin": "29.80%",
            "profit_margin": "25.50%",
            "dividend_yield": "0.55%",
            "recent_headlines": [
                {"headline": f"{ticker} Q2 earnings beat on services strength", "url": ""},
                {"headline": f"AI features drive {ticker} upgrade cycle optimism", "url": ""},
                {"headline": f"{ticker} China revenue down 8%, management cautious", "url": ""},
                {"headline": f"Goldman raises {ticker} price target to $240", "url": ""},
                {"headline": f"{ticker} buyback pace accelerating amid price pullback", "url": ""},
            ],
        },
        "web_news": [
            {"title": f"{ticker} AI integration strategy praised by analysts", "snippet": "Multiple firms upgraded after AI roadmap presentation", "url": ""},
            {"title": f"{ticker} faces EU antitrust scrutiny over App Store", "snippet": "Potential fine of up to 10% of global revenue", "url": ""},
            {"title": f"{ticker} services gross margin hits record 74%", "snippet": "Services now contributes 28% of total revenue", "url": ""},
            {"title": f"Warren Buffett trims {ticker} position again", "snippet": "Berkshire Hathaway cut stake by 13% in Q4", "url": ""},
        ],
        "web_bull_signals": [
            {"title": f"{ticker} AI features to drive next multi-year hardware supercycle", "snippet": "Analysts estimate 600M iPhones eligible for upgrade", "url": ""},
            {"title": f"{ticker} services flywheel accelerating — 1B paid subscriptions", "snippet": "High-margin recurring revenue insulates against hardware cycles", "url": ""},
            {"title": f"{ticker} buyback machine — $110B authorized", "snippet": "Share count declining 3% annually boosting EPS", "url": ""},
        ],
        "web_bear_signals": [
            {"title": f"{ticker} China risk underestimated by Wall Street", "snippet": "Huawei comeback threatens premium segment share", "url": ""},
            {"title": f"EU Digital Markets Act could cost {ticker} billions", "snippet": "App Store changes already reducing services revenue growth rate", "url": ""},
            {"title": f"Hardware saturation: average iPhone replacement cycle now 4.5 years", "snippet": "Upgrade cycle elongation structural not cyclical", "url": ""},
        ],
        "marketwatch_news": [
            {"title": f"{ticker} hits services milestone but hardware remains a concern", "summary": ""},
            {"title": f"Analysts divided on {ticker}'s AI monetization timeline", "summary": ""},
        ],
        "google_finance_news": [
            {"title": f"{ticker} reports Q2 results, beats on EPS"},
            {"title": f"Goldman Sachs reiterates Buy on {ticker}"},
        ],
        "industry_context": [
            {"title": "Consumer electronics sector faces macro headwinds in 2026", "snippet": "Rising consumer debt and slowing discretionary spending", "url": ""},
            {"title": "AI device supercycle expected H2 2026 — analysts", "snippet": "On-device AI features require hardware upgrades", "url": ""},
        ],
        "summary": {"sources_accessed": 3, "total_data_points": 20},
    }


def mock_news(ticker: str) -> dict:
    return {
        "yahoo_finance_headlines": [
            f"{ticker} beats earnings estimates for fourth consecutive quarter",
            f"Analysts raise price targets on {ticker} after strong services growth",
            f"{ticker} announces $110B share buyback program",
            f"Supply chain concerns weigh on {ticker} guidance",
            f"{ticker} Vision Pro shipments below initial expectations",
            f"China sales decline 8% YoY raises concerns for {ticker}",
            f"AI integration to drive next {ticker} upgrade cycle, says analyst",
            f"Warren Buffett reduces {ticker} stake by 13%",
        ],
        "sec_filings_count": 14,
        "total_articles": 8,
        "total_filings": 14,
    }
