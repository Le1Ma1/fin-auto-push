import pandas as pd
from app.db import query_btc_holder_distribution
from app.plot_chart_btc_holder import plot_btc_holder_pie
from app.push.push_etf_chart import upload_to_r2
from app.utils import BTC_HOLDER_COLOR_MAP

def get_flex_bubble_btc_holder(days=7):
    df_hist = query_btc_holder_distribution(days=days)
    df_hist['date'] = pd.to_datetime(df_hist['date'])
    unique_dates = sorted(df_hist['date'].unique())
    print("unique_dates:", unique_dates)
    print("df_hist shape:", df_hist.shape)
    print(df_hist[['date', 'category', 'percent']].tail(20))  # 印最後20筆資料

    if len(unique_dates) >= 2:
        today = unique_dates[-1]
        yesterday = unique_dates[-2]
        df_today = df_hist[df_hist['date'] == today]
        df_yesterday = df_hist[df_hist['date'] == yesterday]
    else:
        today = df_hist['date'].max()
        df_today = df_hist[df_hist['date'] == today]
        df_yesterday = None

    def fmt(val): return f"{float(val):.1f}%"
    def safe(df, cat):
        try:
            return float(df[df['category'] == cat].iloc[0]['percent'])
        except:
            return 0.0
    def format_percent(arrow, sign, diff):
        return f"{arrow}{sign}{abs(diff):.2f}%"

    cats = ["長期持有者", "交易所儲備", "ETF/機構", "未開採", "中央銀行／主權基金", "其他"]

    # 加入簡寫映射
    display_map = {
        "中央銀行／主權基金": "銀行/主權"
    }

    change_lines = []
    if df_yesterday is not None:
        for cat in cats:
            pct_today = safe(df_today, cat)
            pct_yest = safe(df_yesterday, cat)
            diff = pct_today - pct_yest
            if abs(diff) > 0:
                arrow = "🔼" if diff > 0 else "🔽"
                sign = "+" if diff > 0 else ""
                color = "#37D400" if diff > 0 else "#FA5252"
                display_name = display_map.get(cat, cat)
                change_lines.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "■",
                            "size": "md",
                            "flex": 2,
                            "color": BTC_HOLDER_COLOR_MAP.get(cat, "#666666")
                        },
                        {
                            "type": "text",
                            "text": display_name,
                            "size": "sm",
                            "flex": 5,
                            "color": "#F5FAFE"
                        },
                        {
                            "type": "text",
                            "text": format_percent(arrow, sign, diff),
                            "size": "sm",
                            "align": "end",
                            "flex": 6,
                            "color": color,
                            "weight": "bold",
                            "wrap": False,
                            "style": "normal",
                            "gravity": "center",
                            "contents": [],
                        }
                    ],
                    "margin": "sm"
                })

    date_str = pd.to_datetime(today).strftime("%Y-%m-%d")
    img_pie = upload_to_r2(plot_btc_holder_pie(df_today, date_str))

    bubble = {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": img_pie,
            "size": "full",
            "aspectRatio": "8.33:7",
            "aspectMode": "fit"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "contents": [
                {"type": "text", "text": "BTC 六大類持幣分布", "weight": "bold", "size": "xl", "color": "#F5FAFE"},
                {"type": "text", "text": f"日期：{today}", "size": "sm", "color": "#A3E635", "margin": "sm"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#101218",
                    "cornerRadius": "10px",
                    "paddingAll": "8px",      # 改小 padding
                    "margin": "none",        # 改無 margin
                    "contents": (
                        [{"type": "text", "text": "【各分類變動】", "size": "md", "weight": "bold", "color": "#91A4F9"}]
                        + (change_lines if change_lines else [
                            {"type": "text", "text": "今日為最新資料，無前一天比較。", "size": "sm", "color": "#6B7280", "margin": "sm"}
                        ])
                    )
                }
            ]
        }
    }
    return bubble
