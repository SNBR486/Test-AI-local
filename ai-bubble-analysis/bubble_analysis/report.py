from __future__ import annotations
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style='whitegrid')


def _plot_series(df: pd.DataFrame, title: str, fig_path: str):
    plt.figure(figsize=(10, 4))
    df.plot(ax=plt.gca())
    plt.title(title)
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close()


def generate_report(out_path: str, fig_dir: str,
                    c2000: pd.DataFrame, c2008: pd.DataFrame, cAI: pd.DataFrame,
                    results: dict, ai_vals: pd.DataFrame | None = None):
    os.makedirs(fig_dir, exist_ok=True)
    # Plots
    f1 = os.path.join(fig_dir, 'composite_2000.png')
    f2 = os.path.join(fig_dir, 'composite_2008.png')
    f3 = os.path.join(fig_dir, 'composite_ai.png')

    if c2000 is not None and not c2000.empty:
        _plot_series(c2000[['composite']], '2000 Dot-com Composite Score', f1)
    if c2008 is not None and not c2008.empty:
        _plot_series(c2008[['composite']], '2008 Housing/Credit Composite Score', f2)
    if cAI is not None and not cAI.empty:
        _plot_series(cAI[['composite']], '2022-2025 AI Composite Score', f3)

    sim2000 = results.get('similarity_vs_2000', {})
    sim2008 = results.get('similarity_vs_2008', {})

    pred_line = '高风险' if results.get('risk_flag') else '中性'

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("# AI 金融泡沫对比量化报告\n\n")
        f.write(f"生成时间：{datetime.today().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## 结论摘要\n")
        f.write("- 与2000年科网泡沫的相似度（皮尔逊/余弦/DTW-like）："
                f"{sim2000.get('pearson')}, {sim2000.get('cosine')}, {sim2000.get('dtw_like')}\n")
        f.write("- 与2008年房地产/信用周期的相似度（皮尔逊/余弦/DTW-like）："
                f"{sim2008.get('pearson')}, {sim2008.get('cosine')}, {sim2008.get('dtw_like')}\n")
        f.write(f"- 当前AI复合泡沫分数：{results.get('latest_composite')} | 风险判断：{pred_line}\n\n")

        f.write("## 方法与数据\n")
        f.write("- 市场特征：指数与ETF价格动量（3/6/12个月）、动量加速度、成交量相对12个月均值的放大。\n")
        f.write("- 媒体强度：The Guardian 关键词月度篇数（1999年至今）、Google Trends 搜索热度（2004年至今）。\n")
        f.write("- 综合分数：上述标准化特征的加权和；权重偏向价格加速度与媒体热度。\n")
        f.write("- 峰值对齐：取各周期复合分数的峰值前12个月进行窗口对齐并比较。\n\n")

        f.write("## 可视化\n")
        if os.path.exists(f1):
            f.write(f"![](figures/{os.path.basename(f1)})\n\n")
        if os.path.exists(f2):
            f.write(f"![](figures/{os.path.basename(f2)})\n\n")
        if os.path.exists(f3):
            f.write(f"![](figures/{os.path.basename(f3)})\n\n")

        if ai_vals is not None and not ai_vals.empty:
            f.write("## 当前AI龙头估值快照（非历史对比）\n")
            f.write("Ticker | 市值 | Trailing PE | Forward PE | PS(TTM)\n\n")
            for _, row in ai_vals.iterrows():
                cap = row.get('market_cap')
                cap_str = f"{cap/1e12:.2f}T" if cap and cap>=1e12 else (f"{cap/1e9:.1f}B" if cap and cap>=1e9 else str(cap))
                f.write(f"- {row.get('ticker')}: {cap_str}, PE(TTM)={row.get('trailing_pe')}, PE(FWD)={row.get('forward_pe')}, PS={row.get('price_to_sales_ttm')}\n")
            f.write("\n注：估值仅用于刻画当前热度与基本面匹配度，历史估值无法完整可得，故不纳入相似度计算。\n\n")

        f.write("## 局限性与说明\n")
        f.write("- Google Trends 不覆盖2000年前后，科网周期主要依赖报纸与市场数据。\n")
        f.write("- 估值历史数据粒度有限，本工具以价格与媒体热度为主，估值仅作为定性参考。\n")
        f.write("- 本报告仅供研究参考，不构成投资建议。\n")
