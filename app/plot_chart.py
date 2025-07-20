import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import matplotlib.font_manager as fm
from app.utils import human_unit, get_ch_unit_and_div

font_path = 'NotoSansTC-Regular.ttf'   # 字型檔
myfont = fm.FontProperties(fname=font_path)
matplotlib.rcParams['font.family'] = myfont.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

def plot_etf_bar_chart(df, symbol, days=7):
    matplotlib.rcParams['axes.unicode_minus'] = False
    df['date'] = pd.to_datetime(df['date'])
    daily = df.groupby('date').agg({'total_flow_usd': 'first'}).reset_index()
    daily = daily[daily['total_flow_usd'].notnull()]
    daily = daily.tail(days)
    max_val = daily['total_flow_usd'].abs().max()
    unit, unit_div = get_ch_unit_and_div(max_val)
    daily['value_unit'] = daily['total_flow_usd'] / unit_div
    fig, ax = plt.subplots(figsize=(14, 7))
    colors = ['#FA5252' if val < 0 else '#1D9BF6' for val in daily['total_flow_usd']]
    bars = ax.bar(
        daily['date'].dt.strftime('%Y-%m-%d'),
        daily['value_unit'],
        color=colors
    )
    for bar, val in zip(bars, daily['total_flow_usd']):
        color = "#FA5252" if val < 0 else "#1D9BF6"
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.05 if val >= 0 else bar.get_height() - 0.08,
            human_unit(val),
            ha='center', va='bottom' if val >= 0 else 'top', fontsize=16, color=color, fontweight='bold'
        )
    ax.set_title(f"{symbol} ETF 近 {days} 日資金流（{unit}）", fontsize=22, weight='bold')
    ax.set_xlabel("日期", fontsize=17)
    ax.set_ylabel(f"資金流入/流出（{unit}）", fontsize=17)
    ax.grid(axis='y', color='#bbb', linestyle='--', linewidth=1.0, alpha=0.8)
    plt.xticks(rotation=30, ha='right', fontsize=15)
    plt.yticks(fontsize=15)
    plt.tight_layout()
    img_path = f"etf_{symbol}_bar_{daily['date'].min().date()}_{daily['date'].max().date()}.png"
    plt.savefig(img_path, dpi=270, bbox_inches='tight')
    plt.close()
    return img_path

def plot_etf_history_line_chart(df, symbol):
    matplotlib.rcParams['axes.unicode_minus'] = False
    df['date'] = pd.to_datetime(df['date'])
    daily = df.groupby('date').agg({'total_flow_usd': 'first'}).reset_index()
    daily = daily[daily['total_flow_usd'].notnull()]
    daily = daily.sort_values("date")
    max_val = daily['total_flow_usd'].abs().max()
    unit, unit_div = get_ch_unit_and_div(max_val)
    daily['value_unit'] = daily['total_flow_usd'] / unit_div
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(daily['date'], daily['value_unit'], marker='o', linestyle='-', linewidth=3, color='#1D9BF6')
    ax.axhline(0, color='gray', linewidth=1)
    ax.set_title(f"{symbol} ETF 全歷史資金流（{unit}）", fontsize=22, weight='bold')
    ax.set_xlabel("日期", fontsize=17)
    ax.set_ylabel(f"資金流入/流出（{unit}）", fontsize=17)
    plt.xticks(rotation=15, fontsize=13)
    plt.yticks(fontsize=13)
    plt.grid(axis='y', color='#bbb', linestyle='--', linewidth=1.0, alpha=0.8)
    plt.tight_layout()
    img_path = f"etf_{symbol}_history_line.png"
    plt.savefig(img_path, dpi=270, bbox_inches='tight')
    plt.close()
    return img_path

def plot_asset_top10_bar_chart(df, today, unit_str='億', unit_div=1e8):
    import matplotlib.pyplot as plt

    # 先用市值降冪排序
    df_sorted = df.sort_values('market_cap_num', ascending=False).reset_index(drop=True)
    # 名次+資產名稱作為 y 軸
    y_labels = [f"{i+1}. {name}" for i, name in enumerate(df_sorted['name'])]
    bar_values = df_sorted['market_cap_num'] / unit_div

    plt.figure(figsize=(12, 7), facecolor='#191E24')
    ax = plt.gca()
    ax.set_facecolor('#191E24')
    bars = plt.barh(y_labels, bar_values, color='#68A4FF')

    # --- 顏色優化 ---
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    ax.grid(axis='x', color='#444', linestyle='--', linewidth=1, alpha=0.5)

    for i, v in enumerate(bar_values):
        ax.text(v, i, f'{v:,.2f}{unit_str}', color='white', va='center', fontsize=13)

    plt.yticks(color='white', fontsize=13)
    plt.xticks(color='white', fontsize=13)
    plt.title(f"{today} 全球資產市值Top10（{unit_str}美元）", color='white', fontsize=20)
    plt.xlabel(f"市值（{unit_str}美元）", color='white', fontsize=16)
    plt.tight_layout()
    img_path = f'asset_top10_bar_{today}.png'
    plt.savefig(img_path, bbox_inches='tight', transparent=False)
    plt.close()
    return img_path
