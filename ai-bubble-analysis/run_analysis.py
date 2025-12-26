import os
import sys
import json
from datetime import datetime

from bubble_analysis.market import fetch_market_data, build_ai_basket
from bubble_analysis.news_guardian import fetch_guardian_counts
from bubble_analysis.google_trends import fetch_trends
from bubble_analysis.features import (
    prepare_market_features,
    prepare_media_features,
    build_composite_score,
    align_windows,
)
from bubble_analysis.similarity import compute_similarity
from bubble_analysis.report import generate_report
from bubble_analysis.valuations import get_current_valuations


def main():
    out_dir = os.path.join(os.path.dirname(__file__), 'report')
    fig_dir = os.path.join(out_dir, 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    # Date ranges
    r2000 = ("1998-01-01", "2002-12-31")  # dot-com cycle
    r2008 = ("2006-01-01", "2010-12-31")  # housing/credit cycle
    rAI   = ("2022-01-01", datetime.today().strftime("%Y-%m-%d"))

    # Market proxies
    # 2000: NASDAQ Composite (IXIC)
    # 2008: Homebuilders (XHB), Financials (XLF), S&P 500 (^GSPC)
    # 2025 AI: Basket of AI leaders (NVDA, MSFT, GOOGL, META, AVGO, AMD, SMCI)
    tickers_2000 = ["^IXIC"]
    tickers_2008 = ["XHB", "XLF", "^GSPC"]
    ai_basket = ["NVDA", "MSFT", "GOOGL", "META", "AVGO", "AMD", "SMCI"]

    print("Downloading market data ...")
    mkt_2000 = fetch_market_data(tickers_2000, *r2000)
    mkt_2008 = fetch_market_data(tickers_2008, *r2008)
    mkt_ai   = fetch_market_data(ai_basket + ["^IXIC", "^GSPC"], *rAI)

    # Guardian keywords
    kw_2000 = ["dot-com", "internet stocks", "tech bubble", "Nasdaq"]
    kw_2008 = ["subprime", "housing bubble", "mortgage crisis", "Lehman"]
    kw_ai   = ["artificial intelligence", "AI bubble", "generative AI", "NVIDIA"]

    print("Fetching Guardian coverage (may take a few minutes) ...")
    guardian_key = os.environ.get("GUARDIAN_API_KEY", "")
    g2000 = fetch_guardian_counts(kw_2000, r2000[0], r2000[1], api_key=guardian_key)
    g2008 = fetch_guardian_counts(kw_2008, r2008[0], r2008[1], api_key=guardian_key)
    gAI   = fetch_guardian_counts(kw_ai, rAI[0],   rAI[1],   api_key=guardian_key)

    # Google Trends (starts 2004; we skip for 2000)
    print("Fetching Google Trends ...")
    t2008 = fetch_trends(["subprime", "housing bubble", "mortgage crisis"], r2008[0], r2008[1])
    tAI   = fetch_trends(["artificial intelligence", "AI", "ChatGPT", "NVIDIA"], rAI[0], rAI[1])

    # Build features
    print("Computing features ...")
    f2000_mkt = prepare_market_features(mkt_2000)
    f2008_mkt = prepare_market_features(mkt_2008)
    fAI_mkt   = prepare_market_features(mkt_ai)

    f2000_med = prepare_media_features(guardian=g2000)
    f2008_med = prepare_media_features(guardian=g2008, trends=t2008)
    fAI_med   = prepare_media_features(guardian=gAI,   trends=tAI)

    # Composite scores
    c2000 = build_composite_score(f2000_mkt, f2000_med)
    c2008 = build_composite_score(f2008_mkt, f2008_med)
    cAI   = build_composite_score(fAI_mkt,   fAI_med)

    # Align windows around peaks
    c2000_aligned, cAI_2000, peak_2000, peak_ai_ref = align_windows(c2000, cAI, lookback_months=12)
    c2008_aligned, cAI_2008, peak_2008, _ = align_windows(c2008, cAI, lookback_months=12)

    # Similarity metrics
    sim_2000 = compute_similarity(c2000_aligned, cAI_2000)
    sim_2008 = compute_similarity(c2008_aligned, cAI_2008)

    # Prediction heuristic: based on current composite vs historical peak thresholds
    latest_score = float(cAI.tail(1)['composite']) if not cAI.empty else float('nan')
    risk_flag = latest_score > max(c2000['composite'].quantile(0.9), c2008['composite'].quantile(0.9))

    results = {
        'similarity_vs_2000': sim_2000,
        'similarity_vs_2008': sim_2008,
        'latest_composite': latest_score,
        'risk_flag': bool(risk_flag),
        'peaks': {
            '2000_peak': peak_2000.strftime('%Y-%m-%d') if peak_2000 is not None else None,
            '2008_peak': peak_2008.strftime('%Y-%m-%d') if peak_2008 is not None else None,
            'ai_ref': peak_ai_ref.strftime('%Y-%m-%d') if peak_ai_ref is not None else None,
        }
    }

    # Current AI valuations snapshot
    ai_vals = get_current_valuations(ai_basket)
    results['ai_valuations'] = ai_vals.to_dict(orient='records') if ai_vals is not None else []

    # Generate report
    print("Generating report ...")
    ts = datetime.today().strftime('%Y%m%d')
    report_path = os.path.join(out_dir, f"ai_bubble_report_{ts}.md")
    generate_report(report_path, fig_dir, c2000, c2008, cAI, results, ai_vals)

    # Save machine-readable results
    with open(os.path.join(out_dir, f"results_{ts}.json"), 'w') as f:
        json.dump(results, f, indent=2)

    print("Done. Report saved to:", report_path)


if __name__ == "__main__":
    sys.exit(main())
