from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf


def fetch_market_data(tickers, start_date, end_date):
    if isinstance(tickers, str):
        tickers = [tickers]
    data = {}
    for t in tickers:
        try:
            df = yf.download(t, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df is None or df.empty:
                continue
            df = df[['Close', 'Volume']].copy()
            df.columns = pd.MultiIndex.from_product([[t], df.columns])
            data[t] = df
        except Exception:
            continue
    if not data:
        return pd.DataFrame()
    out = pd.concat(data.values(), axis=1).sort_index()
    # Fill missing business days forward for Close, zero for Volume
    out = out.asfreq('B')
    for t in tickers:
        if t in out.columns.get_level_values(0):
            out[(t, 'Close')] = out[(t, 'Close')].ffill()
            out[(t, 'Volume')] = out[(t, 'Volume')].fillna(0)
    return out


def build_ai_basket(prices: pd.DataFrame, tickers):
    # Equal-weight basket price index from Close columns
    close_cols = [(t, 'Close') for t in tickers if (t, 'Close') in prices.columns]
    if not close_cols:
        return pd.Series(dtype=float)
    sub = prices[close_cols].copy()
    # Normalize each to 100 and average
    norm = sub.apply(lambda s: 100 * s / s.dropna().iloc[0])
    basket = norm.mean(axis=1)
    basket.name = 'AI_BASKET'
    return basket
