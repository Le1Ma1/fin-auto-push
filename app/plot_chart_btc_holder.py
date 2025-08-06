import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import pandas as pd
from app.utils import BTC_HOLDER_COLOR_MAP
from app.utils import BTC_HOLDER_COLOR_MAP

def plot_btc_holder_pie(df: pd.DataFrame, date_str: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#191E24")
    ax.set_facecolor("#191E24")
    plt.tight_layout(pad=0)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    labels  = df['category']
    sizes   = df['btc_count']
    explode = [0.05] * len(labels)

    # 依據每個分類找對應顏色
    colors = [BTC_HOLDER_COLOR_MAP.get(cat, "#cccccc") for cat in labels]

    patches, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        explode=explode,
        colors=colors,
        textprops={'fontsize': 14}
    )
    for t in texts + autotexts:
        t.set_color("white")
    ax.set_title(f"BTC 2100萬顆持幣分布（{date_str}）", fontsize=20, color="white")
    img_path = f"btc_holder_pie_{date_str}.png"
    plt.savefig(
        img_path,
        dpi=200,
        bbox_inches='tight',
        pad_inches=0,
        transparent=False
    )
    plt.close(fig)
    return img_path
