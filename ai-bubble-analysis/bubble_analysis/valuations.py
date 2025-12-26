from __future__ import annotations
import pandas as pd
import yfinance as yf


def get_current_valuations(tickers):
    if isinstance(tickers, str):
        tickers = [tickers]
    infos = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.fast_info if hasattr(tk, 'fast_info') else {}
            # Fallback to .info for valuation metrics
            full = getattr(tk, 'info', {}) or {}
            row = {
                'ticker': t,
                'market_cap': full.get('marketCap') or getattr(info, 'market_cap', None),
                'trailing_pe': full.get('trailingPE'),
                'forward_pe': full.get('forwardPE'),
                'price_to_sales_ttm': full.get('priceToSalesTrailing12Months'),
            }
            infos.append(row)
        except Exception:
            continue
    df = pd.DataFrame(infos)
    return df
