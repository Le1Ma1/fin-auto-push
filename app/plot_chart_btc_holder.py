import matplotlib.pyplot as plt
import pandas as pd

def plot_btc_holder_pie(df, date_str):
    """
    畫圓餅圖：六大分類
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    labels = df['category']
    sizes = df['btc_count']
    explode = [0.05] * len(labels)
    colors = ["#6366f1", "#16a34a", "#f59e42", "#f43f5e", "#8b5cf6", "#eab308"]
    patches, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=140, explode=explode, colors=colors, textprops={'fontsize': 14}
    )
    for text in texts + autotexts:
        text.set_color("white")
    ax.set_title(f"BTC 2100萬顆持幣分布（{date_str}）", fontsize=20, color="white")
    fig.patch.set_facecolor("#191E24")
    ax.set_facecolor("#191E24")
    plt.tight_layout()
    img_path = f"btc_holder_pie_{date_str}.png"
    plt.savefig(img_path, dpi=200, bbox_inches="tight", transparent=False)
    plt.close()
    return img_path

def plot_btc_holder_stacked(df_hist):
    """
    畫面積堆疊圖：持幣結構隨時間變化
    """
    df = df_hist.pivot(index='date', columns='category', values='btc_count').fillna(0)
    df = df.sort_index()
    fig, ax = plt.subplots(figsize=(14, 6))
    df.plot.area(ax=ax, alpha=0.8)
    ax.set_title("BTC 六大類持幣分布隨時間變化", fontsize=18, color="white")
    ax.set_xlabel("日期", color="white")
    ax.set_ylabel("BTC 數量", color="white")
    ax.legend(loc='upper left')
    fig.patch.set_facecolor("#191E24")
    ax.set_facecolor("#191E24")
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    plt.tight_layout()
    img_path = "btc_holder_stacked.png"
    plt.savefig(img_path, dpi=200, bbox_inches="tight", transparent=False)
    plt.close()
    return img_path
