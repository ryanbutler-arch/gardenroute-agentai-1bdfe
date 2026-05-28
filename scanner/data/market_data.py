"""Market data fetcher — yfinance as primary source."""
from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)


class MarketData:
    """Fetches and packages all available market data for a ticker."""

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker.upper().strip()
        self._yf = yf.Ticker(self.ticker)
        self._info: dict[str, Any] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        try:
            self._info = self._yf.info or {}
        except Exception:
            self._info = {}
        self._loaded = True

    # ------------------------------------------------------------------
    # Price / Volume history
    # ------------------------------------------------------------------

    def price_history(self, period: str = "5y") -> pd.DataFrame:
        """OHLCV history. Returns empty DataFrame on failure."""
        try:
            df = self._yf.history(period=period, auto_adjust=True)
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def options_data(self) -> dict[str, Any]:
        """Put/call ratio and nearest expiry option chain."""
        result: dict[str, Any] = {"available": False}
        try:
            expirations = self._yf.options
            if not expirations:
                return result
            nearest = expirations[0]
            chain = self._yf.option_chain(nearest)
            calls_volume = chain.calls["volume"].sum()
            puts_volume = chain.puts["volume"].sum()
            total = calls_volume + puts_volume
            result = {
                "available": True,
                "expiration": nearest,
                "calls_volume": int(calls_volume),
                "puts_volume": int(puts_volume),
                "put_call_ratio": round(puts_volume / calls_volume, 3) if calls_volume > 0 else None,
                "sentiment": "bearish" if puts_volume > calls_volume else "bullish",
            }
        except Exception:
            pass
        return result

    # ------------------------------------------------------------------
    # Fundamentals
    # ------------------------------------------------------------------

    def fundamentals(self) -> dict[str, Any]:
        self._load()
        i = self._info
        return {
            "name": i.get("longName") or i.get("shortName", self.ticker),
            "sector": i.get("sector", "N/A"),
            "industry": i.get("industry", "N/A"),
            "country": i.get("country", "N/A"),
            "currency": i.get("currency", "USD"),
            "market_cap": i.get("marketCap"),
            "enterprise_value": i.get("enterpriseValue"),
            # Valuation
            "pe_trailing": i.get("trailingPE"),
            "pe_forward": i.get("forwardPE"),
            "peg": i.get("pegRatio"),
            "pb": i.get("priceToBook"),
            "ps_trailing": i.get("priceToSalesTrailing12Months"),
            "ev_ebitda": i.get("enterpriseToEbitda"),
            "ev_revenue": i.get("enterpriseToRevenue"),
            # Profitability
            "gross_margin": i.get("grossMargins"),
            "operating_margin": i.get("operatingMargins"),
            "profit_margin": i.get("profitMargins"),
            "roe": i.get("returnOnEquity"),
            "roa": i.get("returnOnAssets"),
            # Growth
            "revenue_growth": i.get("revenueGrowth"),
            "earnings_growth": i.get("earningsGrowth"),
            "earnings_quarterly_growth": i.get("earningsQuarterlyGrowth"),
            # Liquidity / leverage
            "current_ratio": i.get("currentRatio"),
            "quick_ratio": i.get("quickRatio"),
            "debt_to_equity": i.get("debtToEquity"),
            "interest_coverage": None,  # computed separately if possible
            "total_cash": i.get("totalCash"),
            "total_debt": i.get("totalDebt"),
            "free_cashflow": i.get("freeCashflow"),
            "operating_cashflow": i.get("operatingCashflow"),
            # Dividends
            "dividend_yield": i.get("dividendYield"),
            "payout_ratio": i.get("payoutRatio"),
            # Share info
            "shares_outstanding": i.get("sharesOutstanding"),
            "shares_short": i.get("sharesShort"),
            "short_ratio": i.get("shortRatio"),
            "short_percent_float": i.get("shortPercentOfFloat"),
            "held_percent_institutions": i.get("heldPercentInstitutions"),
            "held_percent_insiders": i.get("heldPercentInsiders"),
            # Price targets
            "current_price": i.get("currentPrice") or i.get("regularMarketPrice"),
            "52w_high": i.get("fiftyTwoWeekHigh"),
            "52w_low": i.get("fiftyTwoWeekLow"),
            "target_mean_price": i.get("targetMeanPrice"),
            "target_high_price": i.get("targetHighPrice"),
            "target_low_price": i.get("targetLowPrice"),
            "analyst_count": i.get("numberOfAnalystOpinions"),
            "recommendation": i.get("recommendationKey"),
            "beta": i.get("beta"),
            # Description
            "description": i.get("longBusinessSummary", ""),
        }

    def financial_statements(self) -> dict[str, Any]:
        """Annual income statement, balance sheet, cash flow (last 4 years)."""
        result: dict[str, Any] = {}
        try:
            income = self._yf.income_stmt
            if income is not None and not income.empty:
                result["income_stmt"] = income.iloc[:, :4].to_dict()
        except Exception:
            pass
        try:
            balance = self._yf.balance_sheet
            if balance is not None and not balance.empty:
                result["balance_sheet"] = balance.iloc[:, :4].to_dict()
        except Exception:
            pass
        try:
            cashflow = self._yf.cashflow
            if cashflow is not None and not cashflow.empty:
                result["cashflow"] = cashflow.iloc[:, :4].to_dict()
        except Exception:
            pass
        return result

    def insider_transactions(self) -> list[dict]:
        """Recent insider buy/sell transactions."""
        try:
            df = self._yf.insider_transactions
            if df is None or df.empty:
                return []
            df = df.head(20)
            records = []
            for _, row in df.iterrows():
                records.append({
                    "date": str(row.get("Start Date", "")),
                    "insider": str(row.get("Name", "")),
                    "shares": row.get("Shares", 0),
                    "value": row.get("Value", 0),
                    "transaction": str(row.get("Transaction", "")),
                })
            return records
        except Exception:
            return []

    def analyst_recommendations(self) -> list[dict]:
        try:
            df = self._yf.recommendations
            if df is None or df.empty:
                return []
            df = df.tail(10)
            records = []
            for _, row in df.iterrows():
                records.append({
                    "firm": str(row.get("Firm", "")),
                    "grade": str(row.get("To Grade", "")),
                    "action": str(row.get("Action", "")),
                })
            return records
        except Exception:
            return []

    def earnings_history(self) -> list[dict]:
        try:
            df = self._yf.earnings_history
            if df is None or df.empty:
                return []
            records = []
            for _, row in df.tail(8).iterrows():
                records.append({
                    "date": str(row.get("Earnings Date", "")),
                    "eps_estimate": row.get("EPS Estimate"),
                    "eps_actual": row.get("Reported EPS"),
                    "surprise_pct": row.get("Surprise(%)"),
                })
            return records
        except Exception:
            return []
