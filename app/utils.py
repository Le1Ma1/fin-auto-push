import pandas as pd
import datetime

def human_unit(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "0"
    val = float(val)
    units = [("", 1), ("萬", 1e4), ("億", 1e8), ("兆", 1e12)]
    for u, div in reversed(units):
        if abs(val) >= div:
            return f"{val/div:.2f}{u}"
    return str(val)

def get_ch_unit_and_div(max_val):
    if abs(max_val) >= 1e12:
        return '兆', 1e12
    elif abs(max_val) >= 1e8:
        return '億', 1e8
    elif abs(max_val) >= 1e4:
        return '萬', 1e4
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
    now = datetime.datetime.now()
    today = now.date()
    today_ts = pd.Timestamp(today)  # <<<< 加這行
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
