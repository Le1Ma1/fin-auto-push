import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import matplotlib.font_manager as fm
from app.utils import human_unit, get_ch_unit_and_div

font_path = 'NotoSansTC-Regular.ttf'   # 確定你的檔案有在這裡
myfont = fm.FontProperties(fname=font_path)
matplotlib.rcParams['font.family'] = myfont.get_name()     # << 這一行就能全局指定 NotoSansTC
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

def plot_etf_total_line_chart(df, symbol, days=60):
    import matplotlib.pyplot as plt
    import matplotlib
    from app.utils import human_unit, get_ch_unit_and_div

    matplotlib.rcParams['axes.unicode_minus'] = False

    df['date'] = pd.to_datetime(df['date'])
    daily = df.groupby('date').agg({'total_flow_usd': 'first'}).reset_index()
    daily = daily[daily['total_flow_usd'].notnull()]
    daily = daily.tail(days)

    tooltips = []
    df['flow_usd'] = pd.to_numeric(df['flow_usd'], errors='coerce').fillna(0)
    all_days = sorted(df['date'].unique())
    for d in all_days[-days:]:
        sub = df[df['date'] == d]
        lines = []
        for idx, row in sub.iterrows():
            etf = row['etf_ticker']
            fval = float(row['flow_usd'])
            color = "🔵" if fval >= 0 else "🔴"
            lines.append(f"{color}{etf}:{human_unit(fval)}")
        s = '\n'.join(lines)
        tooltips.append(s)

    max_val = daily['total_flow_usd'].abs().max()
    unit, unit_div = get_ch_unit_and_div(max_val)
    daily['value_unit'] = daily['total_flow_usd'] / unit_div

    fig, ax = plt.subplots(figsize=(22, 10))  # 放大畫布
    x = daily['date']
    y = daily['value_unit']

    ax.plot(x, y, marker='o', linestyle='-', color='#1D9BF6', linewidth=4, markersize=12)
    ax.axhline(0, color='#888', linestyle='--', linewidth=1.8)
    for idx, (xi, yi, val) in enumerate(zip(x, y, daily['total_flow_usd'])):
        color = "#FA5252" if val < 0 else "#1D9BF6"
        tt = tooltips[idx] if idx < len(tooltips) else ""
        ax.text(
            xi, yi + (0.07 if val >= 0 else -0.1),
            f"{human_unit(val)}\n{tt}",
            fontsize=13, ha='center', va='bottom' if val >= 0 else 'top',
            color=color, fontweight='bold',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, boxstyle='round,pad=0.3')
        )
    ax.set_title(f"{symbol} ETF 長期資金流趨勢（{unit}）", fontsize=26, weight='bold')
    ax.set_xlabel("日期", fontsize=20)
    ax.set_ylabel(f"日流入/流出（{unit}）", fontsize=20)
    plt.xticks(rotation=30, ha='right', fontsize=14)
    plt.yticks(fontsize=15)
    ax.grid(True, linestyle='--', alpha=0.8)
    plt.tight_layout()
    img_path = f"etf_{symbol}_line_{daily['date'].min().date()}_{daily['date'].max().date()}.png"
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
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

    fig, ax = plt.subplots(figsize=(20, 8))

    # 折線
    ax.plot(daily['date'], daily['value_unit'], marker='o', linestyle='-', color='#1D9BF6', linewidth=3, markersize=7)

    # 標題 & 標籤
    ax.set_title(f"{symbol} ETF 全歷史資金流趨勢（{unit}）", fontsize=26, weight='bold')
    ax.set_xlabel("日期", fontsize=17)
    ax.set_ylabel(f"日流入/流出（{unit}）", fontsize=17)
    ax.grid(True, linestyle='--', alpha=0.7)

    # x軸標籤只標大節點
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator())  # 每月一標
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=30, ha='right', fontsize=13)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    # 起始&終點、最大值加註
    start_day = daily['date'].min().strftime('%Y-%m-%d')
    end_day = daily['date'].max().strftime('%Y-%m-%d')
    ax.text(daily['date'].iloc[0], daily['value_unit'].iloc[0], f"{start_day}\n{human_unit(daily['total_flow_usd'].iloc[0])}", 
            ha='left', va='bottom', fontsize=12, color='#222', fontweight='bold')
    ax.text(daily['date'].iloc[-1], daily['value_unit'].iloc[-1], f"{end_day}\n{human_unit(daily['total_flow_usd'].iloc[-1])}", 
            ha='right', va='bottom', fontsize=12, color='#222', fontweight='bold')

    img_path = f"etf_{symbol}_history_line_{start_day}_{end_day}.png"
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.close()
    return img_path