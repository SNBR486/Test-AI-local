from __future__ import annotations
import pandas as pd
from pytrends.request import TrendReq


def fetch_trends(keywords, start_date: str, end_date: str) -> pd.DataFrame:
    # Google Trends monthly interest over time
    if isinstance(keywords, str):
        keywords = [keywords]
    timeframe = f"{start_date} {end_date}"
    pytrends = TrendReq(hl='en-US', tz=0)
    frames = []
    for kw in keywords:
        try:
            pytrends.build_payload([kw], cat=0, timeframe=timeframe, geo='', gprop='')
            df = pytrends.interest_over_time()
            if df is None or df.empty:
                continue
            s = df[kw].copy()
            s.index = pd.to_datetime(s.index)
            s = s.resample('M').mean().round(2)
            s.name = kw
            frames.append(s)
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, axis=1).fillna(0).sort_index()
    return out
