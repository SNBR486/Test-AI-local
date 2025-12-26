AI Bubble Comparative Analysis Toolkit

This toolkit quantifies and compares the 2000 dot-com bubble, the 2008 housing/credit crisis, and the 2025 AI cycle using:
- Market data (indices, ETFs, and selected stocks)
- Google Trends interest (2004-present)
- Newspaper coverage via The Guardian Content API (1999-present)

It computes composite "bubble scores," similarity to past peaks, and a forward-looking risk assessment.

How to run
1) Install dependencies: pip install -r requirements.txt
2) Ensure GUARDIAN_API_KEY is set in your environment (optional but recommended)
3) Run: python run_analysis.py
4) Outputs: report/*.md and report/figures/*.png

Notes
- Google Trends only starts in 2004. For the 2000 episode we rely on newspapers + market data.
- Guardian coverage is used as a proxy for media intensity. If API quota is an issue, the script will degrade gracefully.
- This is an analytical tool for research; it is not investment advice.
