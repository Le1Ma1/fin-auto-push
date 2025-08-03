import os
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import matplotlib.font_manager as fm
from app.utils import human_unit, get_ch_unit_and_div

def get_font_properties():
    try:
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'NotoSansTC-Regular.ttf'))
        print(f"[DEBUG] font path: {font_path}")
        if os.path.isfile(font_path):
            fm.fontManager.addfont(font_path)
            plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()
            print(f"[INFO] 使用自訂字型：{font_path}")
            return fm.FontProperties(fname=font_path)
        else:
            print(f"[WARN] 字型檔不存在，使用系統預設字型: {font_path}")
            plt.rcParams['font.family'] = 'DejaVu Sans'
            return fm.FontProperties()
    except Exception as e:
        print(f"[ERROR] 載入字型失敗: {e}")
        return fm.FontProperties()
myfont = get_font_properties()
plt.rcParams['axes.unicode_minus'] = False

def plot_etf_bar_chart(df: pd.DataFrame, symbol: str, days: int = 30) -> str:
    """
    畫 ETF 近 N 日資金流長條圖 (2:1)，並輸出 PNG 檔。
    """
    # 1. 複製資料並取最近 days 筆
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    daily = (
        df.groupby('date')
          .agg({'total_flow_usd': 'first'})
          .reset_index()
          .dropna(subset=['total_flow_usd'])
    )
    daily = daily.tail(days)

    # 2. 計算最大值單位 (e.g. 億/兆)
    max_val = daily['total_flow_usd'].abs().max()
    unit, unit_div = get_ch_unit_and_div(max_val)
    daily['value_unit'] = daily['total_flow_usd'] / unit_div

    # 3. 建立 2:1 的畫布 (寬×高 = 12×6 吋)
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#191E24')
    ax.set_facecolor('#191E24')

    # 4. 完全移除所有 Matplotlib 預設邊距
    plt.tight_layout(pad=0)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # 5. 畫長條圖
    colors = ['#FA5252' if val < 0 else '#1D9BF6' for val in daily['total_flow_usd']]
    bars   = ax.bar(daily['date'].dt.strftime('%Y-%m-%d'),
                    daily['value_unit'],
                    color=colors)

    # 6. 在條尾加標籤
    for bar, val in zip(bars, daily['total_flow_usd']):
        label = f"{human_unit(val)}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (0.05 if val >= 0 else -0.08),
            label,
            ha='center',
            va='bottom' if val >= 0 else 'top',
            fontsize=14,
            color=("#1D9BF6" if val >= 0 else "#FA5252"),
            fontweight='bold'
        )

    # 7. 標題與軸標籤
    ax.set_title(f"{symbol} ETF 近 {days} 日資金流（{unit}）",
                 fontsize=20, color='white')
    ax.set_xlabel("日期", fontsize=16, color='white')
    ax.set_ylabel(f"資金流入/流出（{unit}）", fontsize=16, color='white')
    ax.grid(axis='y', color='#555', linestyle='--', alpha=0.5)
    plt.xticks(rotation=30, ha='right', fontsize=13, color='white')
    plt.yticks(fontsize=13, color='white')
    for spine in ax.spines.values():
        spine.set_color('white')

    # 8. 輸出 PNG，去除所有外圍空白
    img_path = f"etf_{symbol}_bar_{daily['date'].min().date()}_{daily['date'].max().date()}.png"
    plt.savefig(
        img_path,
        dpi=270,
        bbox_inches='tight',  # 緊貼內容裁剪
        pad_inches=0,         # 無額外邊距
        transparent=False
    )
    plt.close(fig)
    return img_path

def plot_etf_history_line_chart(df, symbol):
    matplotlib.rcParams['axes.unicode_minus'] = False
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    daily = df.groupby('date').agg({'total_flow_usd': 'first'}).reset_index()
    daily = daily[daily['total_flow_usd'].notnull()]
    daily = daily.sort_values("date")
    max_val = daily['total_flow_usd'].abs().max()
    unit, unit_div = get_ch_unit_and_div(max_val)
    daily['value_unit'] = daily['total_flow_usd'] / unit_div
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#191E24')
    ax.set_facecolor('#191E24')
    ax.plot(daily['date'], daily['value_unit'], marker='o', linestyle='-', linewidth=3, color='#1D9BF6')
    ax.axhline(0, color='gray', linewidth=1)
    ax.set_title(f"{symbol} ETF 全歷史資金流（{unit}）", fontsize=22, weight='bold', color='white')
    ax.set_xlabel("日期", fontsize=17, color='white')
    ax.set_ylabel(f"資金流入/流出（{unit}）", fontsize=17, color='white')
    plt.xticks(rotation=15, fontsize=13, color='white')
    plt.yticks(fontsize=13, color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    for spine in ax.spines.values():
        spine.set_color('white')
    plt.grid(axis='y', color='#bbb', linestyle='--', linewidth=1.0, alpha=0.4)
    plt.tight_layout()
    img_path = f"etf_{symbol}_history_line.png"
    plt.savefig(img_path, dpi=270, bbox_inches='tight', transparent=False)
    plt.close()
    return img_path

import matplotlib.pyplot as plt
import pandas as pd

def plot_asset_top10_bar_chart(df: pd.DataFrame, today: str,
                               unit_str: str = '兆',
                               unit_div: float = 1e12) -> str:
    """
    畫全球資產市值 Top10 橫條圖，輸出橫向長條 (2:1) PNG。
    """
    # 1. 建立 12x6 吋的畫布 ⇒ 12/6 = 2:1
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#191E24')
    ax.set_facecolor('#191E24')

    # 2. 移除所有 Matplotlib 邊距
    plt.tight_layout(pad=0)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # 3. 資料處理
    df_sorted = df.sort_values('symbol_cap_num', ascending=False).reset_index(drop=True)
    y_labels   = [f"{i+1:02d}. {name}" for i, name in enumerate(df_sorted['name'])]
    bar_vals   = df_sorted['symbol_cap_num'] / unit_div

    # 4. 畫水平橫條
    bars = ax.barh(y_labels, bar_vals, color='#68A4FF')

    # 5. 格線 & 坐標軸樣式
    ax.grid(axis='x', color='#444', linestyle='--', linewidth=1, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

    # 6. 條末標註數值
    for i, v in enumerate(bar_vals):
        ax.text(
            v, i,
            f"{v:,.2f}{unit_str}",  # e.g. "22.60兆"
            va='center', fontsize=13, color='white'
        )

    # 7. 標題與軸標籤
    ax.set_title(f"{today} 全球資產市值 Top10（{unit_str} 美元）",
                 fontsize=20, pad=10, color='white')
    ax.set_xlabel(f"市值（{unit_str} 美元）", fontsize=16)

    # 8. 輸出 PNG，去除所有空白
    img_path = f"asset_top10_bar_{today}.png"
    plt.savefig(
        img_path,
        dpi=200,
        bbox_inches='tight',
        pad_inches=0,
        transparent=False
    )
    plt.close(fig)
    return img_path
