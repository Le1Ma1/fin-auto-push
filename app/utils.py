import pandas as pd
import datetime
import pytz

def human_unit(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "0"
    val = float(val)
    units = [("", 1), ("萬", 1e4), ("億", 1e8), ("兆", 1e12)]
    for u, div in reversed(units):
        if abs(val) >= div:
            return f"{val/div:.2f}{u}"
    return str(val)

def get_ch_unit_and_div(val):
    if abs(val) >= 1e12:
        return '兆', 1e12
    elif abs(val) >= 1e9:
        return '十億', 1e9
    elif abs(val) >= 1e8:
        return '億', 1e8
    elif abs(val) >= 1e6:
        return '百萬', 1e6
    else:
        return '元', 1

def etf_flex_table(etf_summary):
    rows = []
    for ticker, flow in etf_summary.items():
        color = "#FA5252" if flow < 0 else "#1D9BF6"
        rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": ticker, "size": "sm", "flex": 3, "color": "#666666"},
                {"type": "text", "text": f"{human_unit(flow)}", "size": "sm", "align": "end", "flex": 7, "color": color}
            ],
            "margin": "sm"
        })
    return rows

def etf_flex_table_single_day(df):
    df['flow_usd'] = pd.to_numeric(df['flow_usd'], errors='coerce').fillna(0)
    df_day = df[df['date'] == df['date'].max()]
    etf_summary = df_day.groupby('etf_ticker')['flow_usd'].sum().sort_values(ascending=False)
    rows = []
    for ticker, flow in etf_summary.items():
        color = "#FA5252" if flow < 0 else "#1D9BF6"
        rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": ticker, "size": "sm", "flex": 3, "color": "#666666"},
                {"type": "text", "text": f"{human_unit(flow)}", "size": "sm", "align": "end", "flex": 7, "color": color}
            ],
            "margin": "sm"
        })
    return rows

def fill_bar_chart_dates(df_bar_raw, days=10):
    end = df_bar_raw['date'].max()
    date_range = pd.date_range(end=end, periods=days)
    df_empty = pd.DataFrame({'date': date_range})
    df_bar = pd.merge(df_empty, df_bar_raw, how='left', on='date')
    df_bar['flow_usd'] = df_bar['flow_usd'].fillna(0)
    df_bar['total_flow_usd'] = df_bar['total_flow_usd'].fillna(0)
    df_bar = df_bar.sort_values('date')
    return df_bar

def is_weekend(day):
    """判斷日期是否週末（六日）"""
    if isinstance(day, pd.Timestamp):
        return day.weekday() >= 5
    elif isinstance(day, datetime.date):
        return day.weekday() >= 5
    return False

def get_latest_safe_etf_date(df):
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.datetime.now(tz)
    today = now.date()
    today_ts = pd.Timestamp(today)
    two_pm = now.replace(hour=14, minute=0, second=0, microsecond=0)
    df['date'] = pd.to_datetime(df['date'])
    all_days = sorted(df['date'].unique(), reverse=True)
    if now >= two_pm:
        for day in all_days:
            if day < today_ts and not is_weekend(day):
                return day
    count = 0
    for day in all_days:
        if day < today_ts and not is_weekend(day):
            count += 1
            if count == 2:
                return day
    return None

def get_recent_n_days_settled(df, target_date, n=14):
    """給定已確認的 target_date，往前取 n 天的完整日"""
    df['date'] = pd.to_datetime(df['date'])
    start_date = target_date - pd.Timedelta(days=n-1)
    return df[(df['date'] >= start_date) & (df['date'] <= target_date)]

def get_all_settled_until(df, target_date):
    """抓所有小於等於 target_date 的資料，安全去除假日/未結算日"""
    df['date'] = pd.to_datetime(df['date'])
    return df[df['date'] <= pd.Timestamp(target_date)]

def get_clean_name(row):
    name = row['name']
    if '(' in name:
        name = name.split('(')[0].strip()
    if name.upper() in ['BITCOIN', 'BTC', 'ETH', 'GOLD', 'SILVER']:
        name = row['symbol']
    return name

def generate_btc_holder_highlight(df_today, df_yesterday=None):
    """
    自動根據持幣六分類產生本日亮點摘要（台灣中文），可 plug-in 進 Flex message。
    df_today, df_yesterday: 需為相同 DataFrame 格式，含 category, btc_count, percent 欄位
    """
    mapping = {
        "長期持有者": "長期持有者",
        "交易所儲備": "交易所儲備",
        "ETF/機構": "ETF/機構",
        "未開採": "未開採",
        "中央銀行／主權基金": "中央銀行/主權基金",
        "其他": "其他"
    }
    # 取出三大主分類的百分比
    lth = df_today[df_today['category'] == "長期持有者"].iloc[0]['percent']
    exch = df_today[df_today['category'] == "交易所儲備"].iloc[0]['percent']
    etf = df_today[df_today['category'] == "ETF/機構"].iloc[0]['percent']

    def fmt(val): return f"{float(val):.1f}%"

    highlight_lines = []
    highlight_lines.append(
        f"長期持有者占比高達 {fmt(lth)}，顯示籌碼極度集中於信仰者手中。")
    highlight_lines.append(
        f"交易所儲備僅佔 {fmt(exch)}，市場拋壓相對有限。")
    highlight_lines.append(
        f"ETF/機構持有 {fmt(etf)}，機構參與持續提升。")

    # 進階：比較昨日，若有 df_yesterday，檢查大變動
    if df_yesterday is not None:
        for cat, name in mapping.items():
            pct_today = float(df_today[df_today['category'] == cat].iloc[0]['percent'])
            pct_yest = float(df_yesterday[df_yesterday['category'] == cat].iloc[0]['percent'])
            diff = pct_today - pct_yest
            if abs(diff) >= 0.3:
                arrow = "▲" if diff > 0 else "▼"
                sign = "+" if diff > 0 else ""
                highlight_lines.append(
                    f"{name}今日占比{arrow}{sign}{diff:.1f}%")
    return "\n".join(highlight_lines)
