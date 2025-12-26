from __future__ import annotations
import os
from datetime import datetime
import time
import requests
import pandas as pd

BASE_URL = "https://content.guardianapis.com/search"


def _guardian_query(query: str, from_date: str, to_date: str, api_key: str = ""):
    page = 1
    page_size = 200
    total = None
    results = []
    params = {
        'q': query,
        'from-date': from_date,
        'to-date': to_date,
        'page-size': page_size,
        'page': page,
        'api-key': api_key or 'test',  # Guardian allows limited test key
        'show-fields': 'trailText',
    }
    while True:
        params['page'] = page
        r = requests.get(BASE_URL, params=params, timeout=30)
        if r.status_code != 200:
            break
        data = r.json()
        resp = data.get('response', {})
        if total is None:
            total = resp.get('total', 0)
        results.extend(resp.get('results', []))
        if resp.get('currentPage', 1) >= resp.get('pages', 1):
            break
        page += 1
        time.sleep(0.2)
    # Build DataFrame with dates
    rows = []
    for item in results:
        pub_date = item.get('webPublicationDate')
        try:
            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
        except Exception:
            continue
        rows.append({'date': dt.date(), 'id': item.get('id')})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
    counts = df.groupby('month').size().rename(query)
    return counts


def fetch_guardian_counts(keywords, from_date: str, to_date: str, api_key: str = "") -> pd.DataFrame:
    if isinstance(keywords, str):
        keywords = [keywords]
    series = []
    for kw in keywords:
        try:
            s = _guardian_query(kw, from_date, to_date, api_key)
            if s is None or s.empty:
                continue
            series.append(s)
        except Exception:
            continue
    if not series:
        return pd.DataFrame()
    out = pd.concat(series, axis=1).fillna(0).sort_index()
    return out
