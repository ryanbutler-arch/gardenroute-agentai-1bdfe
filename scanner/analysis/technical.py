"""Technical analysis — indicators computed from OHLCV data."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=window, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(window=window, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = _ema(series, 12)
    ema26 = _ema(series, 26)
    macd_line = ema12 - ema26
    signal = _ema(macd_line, 9)
    histogram = macd_line - signal
    return macd_line, signal, histogram


def _bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = _sma(series, window)
    std = series.rolling(window=window, min_periods=1).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=window, min_periods=1).mean()


def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


def _stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3):
    lowest_low = low.rolling(window=k_window, min_periods=1).min()
    highest_high = high.rolling(window=k_window, min_periods=1).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-9)
    d = k.rolling(window=d_window, min_periods=1).mean()
    return k, d


def _support_resistance(close: pd.Series, window: int = 20, n_levels: int = 3) -> dict:
    """Find rough support/resistance via local min/max."""
    highs, lows = [], []
    arr = close.values
    for i in range(window, len(arr) - window):
        if arr[i] == max(arr[i - window: i + window]):
            highs.append(arr[i])
        if arr[i] == min(arr[i - window: i + window]):
            lows.append(arr[i])
    return {
        "resistance": [round(float(v), 4) for v in sorted(highs, reverse=True)[:n_levels]],
        "support": [round(float(v), 4) for v in sorted(lows)[:n_levels]],
    }


def run(df: pd.DataFrame) -> dict[str, Any]:
    """Compute all technical indicators and return a structured summary."""
    if df.empty or len(df) < 20:
        return {"error": "Insufficient price data for technical analysis"}

    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    volume = df["Volume"].squeeze()

    # Moving averages
    sma20 = _sma(close, 20).iloc[-1]
    sma50 = _sma(close, 50).iloc[-1]
    sma200 = _sma(close, 200).iloc[-1]
    ema12 = _ema(close, 12).iloc[-1]
    ema26 = _ema(close, 26).iloc[-1]

    current = close.iloc[-1]
    prev_week = close.iloc[-6] if len(close) >= 6 else close.iloc[0]
    prev_month = close.iloc[-22] if len(close) >= 22 else close.iloc[0]
    prev_3m = close.iloc[-66] if len(close) >= 66 else close.iloc[0]
    prev_6m = close.iloc[-132] if len(close) >= 132 else close.iloc[0]
    prev_year = close.iloc[-252] if len(close) >= 252 else close.iloc[0]
    prev_3y = close.iloc[-756] if len(close) >= 756 else close.iloc[0]

    # Momentum
    rsi14 = _rsi(close).iloc[-1]
    macd_line, signal_line, histogram = _macd(close)
    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    hist_val = histogram.iloc[-1]
    stoch_k, stoch_d = _stochastic(high, low, close)

    # Volatility
    bb_upper, bb_mid, bb_lower = _bollinger(close)
    bb_width = (bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_mid.iloc[-1] if bb_mid.iloc[-1] else 0
    bb_pct = (current - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1] + 1e-9)
    atr14 = _atr(high, low, close).iloc[-1]
    atr_pct = atr14 / current if current else 0

    # Volatility (historical)
    daily_returns = close.pct_change().dropna()
    vol_30d = daily_returns.iloc[-22:].std() * np.sqrt(252) if len(daily_returns) >= 22 else None
    vol_90d = daily_returns.iloc[-66:].std() * np.sqrt(252) if len(daily_returns) >= 66 else None

    # Volume trend
    avg_vol_20 = volume.iloc[-20:].mean()
    avg_vol_50 = volume.iloc[-50:].mean() if len(volume) >= 50 else avg_vol_20
    vol_recent = volume.iloc[-5:].mean()
    obv_series = _obv(close, volume)
    obv_trend = "rising" if obv_series.iloc[-1] > obv_series.iloc[-20] else "falling"

    # Support / resistance
    sr = _support_resistance(close)

    # Trend classification
    def trend(price, ma_short, ma_long):
        if price > ma_short > ma_long:
            return "strong_uptrend"
        elif price > ma_short:
            return "uptrend"
        elif price < ma_short < ma_long:
            return "strong_downtrend"
        elif price < ma_short:
            return "downtrend"
        return "sideways"

    price_trend = trend(current, sma50, sma200)

    # Golden / death cross
    cross = None
    if len(close) >= 200:
        sma50_series = _sma(close, 50)
        sma200_series = _sma(close, 200)
        if sma50_series.iloc[-1] > sma200_series.iloc[-1] and sma50_series.iloc[-20] < sma200_series.iloc[-20]:
            cross = "golden_cross"
        elif sma50_series.iloc[-1] < sma200_series.iloc[-1] and sma50_series.iloc[-20] > sma200_series.iloc[-20]:
            cross = "death_cross"

    return {
        "current_price": round(float(current), 4),
        "trend": price_trend,
        "cross_signal": cross,
        "moving_averages": {
            "sma20": round(float(sma20), 4),
            "sma50": round(float(sma50), 4),
            "sma200": round(float(sma200), 4),
            "ema12": round(float(ema12), 4),
            "ema26": round(float(ema26), 4),
            "price_vs_sma20_pct": round((current / sma20 - 1) * 100, 2),
            "price_vs_sma50_pct": round((current / sma50 - 1) * 100, 2),
            "price_vs_sma200_pct": round((current / sma200 - 1) * 100, 2),
        },
        "momentum": {
            "rsi_14": round(float(rsi14), 2),
            "rsi_signal": "overbought" if rsi14 > 70 else ("oversold" if rsi14 < 30 else "neutral"),
            "macd": round(float(macd_val), 4),
            "macd_signal": round(float(signal_val), 4),
            "macd_histogram": round(float(hist_val), 4),
            "macd_crossover": "bullish" if macd_val > signal_val else "bearish",
            "stoch_k": round(float(stoch_k.iloc[-1]), 2),
            "stoch_d": round(float(stoch_d.iloc[-1]), 2),
            "stoch_signal": "overbought" if stoch_k.iloc[-1] > 80 else ("oversold" if stoch_k.iloc[-1] < 20 else "neutral"),
        },
        "volatility": {
            "atr_14": round(float(atr14), 4),
            "atr_pct": round(float(atr_pct) * 100, 2),
            "bb_width_pct": round(float(bb_width) * 100, 2),
            "bb_position_pct": round(float(bb_pct) * 100, 2),
            "bb_signal": "near_upper_band" if bb_pct > 0.8 else ("near_lower_band" if bb_pct < 0.2 else "mid_range"),
            "historical_vol_30d_annualized": round(float(vol_30d) * 100, 2) if vol_30d else None,
            "historical_vol_90d_annualized": round(float(vol_90d) * 100, 2) if vol_90d else None,
        },
        "volume": {
            "avg_20d": int(avg_vol_20),
            "avg_50d": int(avg_vol_50),
            "recent_5d_avg": int(vol_recent),
            "volume_vs_avg_pct": round((vol_recent / avg_vol_20 - 1) * 100, 2),
            "obv_trend": obv_trend,
        },
        "price_performance": {
            "1w_pct": round((current / prev_week - 1) * 100, 2),
            "1m_pct": round((current / prev_month - 1) * 100, 2),
            "3m_pct": round((current / prev_3m - 1) * 100, 2),
            "6m_pct": round((current / prev_6m - 1) * 100, 2),
            "1y_pct": round((current / prev_year - 1) * 100, 2),
            "3y_pct": round((current / prev_3y - 1) * 100, 2),
        },
        "support_resistance": sr,
        "data_points": len(close),
    }
