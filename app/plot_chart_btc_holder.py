import matplotlib.pyplot as plt
import pandas as pd

def plot_btc_holder_pie(df: pd.DataFrame, date_str: str) -> str:
    """
    畫 BTC 六大類持幣分布圓餅圖，輸出正方形 (1:1) PNG。
    """
    # 1. 建立 8x8 吋的正方形畫布 ⇒ 8/8 = 1:1
    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#191E24")
    ax.set_facecolor("#191E24")

    # 2. 移除所有 Matplotlib 預設邊距
    plt.tight_layout(pad=0)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # 3. 準備資料
    labels  = df['category']
    sizes   = df['btc_count']
    explode = [0.05] * len(labels)

    # 4. 畫圓餅
    patches, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        explode=explode,
        colors=["#6366f1", "#16a34a", "#f59e42", "#f43f5e", "#8b5cf6", "#eab308"],
        textprops={'fontsize': 14}
    )

    # 5. 文字改白色
    for t in texts + autotexts:
        t.set_color("white")

    # 6. 標題
    ax.set_title(f"BTC 2100萬顆持幣分布（{date_str}）",
                 fontsize=20, color="white")

    # 7. 輸出 PNG，去除所有外白
    img_path = f"btc_holder_pie_{date_str}.png"
    plt.savefig(
        img_path,
        dpi=200,
        bbox_inches='tight',  # 緊貼內容
        pad_inches=0,         # 無額外邊距
        transparent=False
    )
    plt.close(fig)
    return img_path
