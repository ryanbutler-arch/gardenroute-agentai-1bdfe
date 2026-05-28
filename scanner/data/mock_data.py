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
