from __future__ import annotations
import pandas as pd
import numpy as np


def _pct_change_rolling(s: pd.Series, months: int) -> pd.Series:
    return s.pct_change(months)


def prepare_market_features(prices: pd.DataFrame) -> pd.DataFrame:
    if prices is None or prices.empty:
        return pd.DataFrame()
    # Work monthly
    monthly = prices.copy()
    monthly.index = pd.to_datetime(monthly.index)
    monthly = monthly.resample('M').last()

    # Momentum features from Close
    feat = pd.DataFrame(index=monthly.index)
    close_cols = [c for c in monthly.columns if c[1] == 'Close']
    vol_cols = [c for c in monthly.columns if c[1] == 'Volume']

    if close_cols:
        # Average across available Close columns for a broad index
        agg_close = monthly[close_cols].mean(axis=1)
        feat['mom_3m'] = _pct_change_rolling(agg_close, 3)
        feat['mom_6m'] = _pct_change_rolling(agg_close, 6)
        feat['mom_12m'] = _pct_change_rolling(agg_close, 12)
        # Acceleration: 3m - 12m
        feat['accel'] = feat['mom_3m'] - feat['mom_12m']

    if vol_cols:
        agg_vol = monthly[vol_cols].mean(axis=1)
        vol_ma = agg_vol.rolling(12, min_periods=3).mean()
        feat['vol_spike'] = (agg_vol / vol_ma) - 1.0

    # Z-score normalize each feature
    for c in feat.columns:
        x = feat[c]
        feat[c] = (x - x.mean()) / (x.std(ddof=0) + 1e-9)

    feat = feat.dropna()
    return feat


def prepare_media_features(guardian: pd.DataFrame | None = None,
                           trends: pd.DataFrame | None = None) -> pd.DataFrame:
    frames = []
    if guardian is not None and not guardian.empty:
        g = guardian.copy()
        g.index = pd.to_datetime(g.index)
        g = g.resample('M').sum()
        # Use total keyword volume and z-score
        g['guardian_volume'] = g.sum(axis=1)
        gv = g['guardian_volume']
        g['guardian_z'] = (gv - gv.mean()) / (gv.std(ddof=0) + 1e-9)
        frames.append(g[['guardian_z']])
    if trends is not None and not trends.empty:
        t = trends.copy()
        t.index = pd.to_datetime(t.index)
        t = t.resample('M').mean()
        t['trends_volume'] = t.sum(axis=1)
        tv = t['trends_volume']
        t['trends_z'] = (tv - tv.mean()) / (tv.std(ddof=0) + 1e-9)
        frames.append(t[['trends_z']])
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, axis=1).sort_index()
    return out


def build_composite_score(market_feat: pd.DataFrame, media_feat: pd.DataFrame) -> pd.DataFrame:
    # Weighted sum of normalized features
    if market_feat is None or market_feat.empty:
        market_feat = pd.DataFrame(index=media_feat.index if media_feat is not None else None)
    if media_feat is None or media_feat.empty:
        media_feat = pd.DataFrame(index=market_feat.index)

    idx = market_feat.index.union(media_feat.index)
    m = market_feat.reindex(idx).fillna(0)
    med = media_feat.reindex(idx).fillna(0)

    weights = {
        'mom_12m': 0.25,
        'mom_6m': 0.10,
        'mom_3m': 0.10,
        'accel': 0.20,
        'vol_spike': 0.10,
        'guardian_z': 0.125,
        'trends_z': 0.125,
    }
    composite = pd.Series(0.0, index=idx)
    for k, w in weights.items():
        if k in m.columns:
            composite = composite.add(w * m[k], fill_value=0)
        elif k in med.columns:
            composite = composite.add(w * med[k], fill_value=0)
    out = pd.DataFrame({'composite': composite}).sort_index()
    return out


def align_windows(ref: pd.DataFrame, current: pd.DataFrame, lookback_months: int = 12):
    # Find peak in reference composite and current composite windows
    if ref is None or ref.empty or current is None or current.empty:
        return ref, current, None, None
    ref_peak_date = ref['composite'].idxmax()
    cur_peak_date = current['composite'].idxmax()

    ref_win_start = ref_peak_date - pd.DateOffset(months=lookback_months)
    cur_win_start = cur_peak_date - pd.DateOffset(months=lookback_months)

    ref_slice = ref.loc[ref_win_start:ref_peak_date]
    cur_slice = current.loc[cur_win_start:cur_peak_date]

    return ref_slice, cur_slice, ref_peak_date, cur_peak_date
