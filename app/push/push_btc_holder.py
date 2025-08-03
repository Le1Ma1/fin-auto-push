from app.db import query_btc_holder_distribution
from app.plot_chart_btc_holder import plot_btc_holder_pie
from app.push.push_etf_chart import upload_to_r2
from app.utils import BTC_HOLDER_COLOR_MAP

def get_flex_bubble_btc_holder(days=1):
    df_hist = query_btc_holder_distribution(days=days)
    today = df_hist['date'].max().strftime("%Y-%m-%d")
    df_today = df_hist[df_hist['date'] == df_hist['date'].max()]
    if len(df_hist['date'].unique()) >= 2:
        yesterday = sorted(df_hist['date'].unique())[-2]
        df_yesterday = df_hist[df_hist['date'] == yesterday]
    else:
        df_yesterday = None

    def fmt(val): return f"{float(val):.1f}%"
    def safe(df, cat):
        try:
            return float(df[df['category'] == cat].iloc[0]['percent'])
        except:
            return 0.0
    def format_percent(arrow, sign, diff):
        s = f"{arrow}{sign}{abs(diff):.2f}%"
        return s.rjust(8)

    highlight_lines = [
        f"💡 長期持有者：{fmt(safe(df_today, '長期持有者'))}（籌碼極度集中）",
        f"🏦 交易所儲備：{fmt(safe(df_today, '交易所儲備'))}（拋壓有限）",
        f"🏢 ETF/機構：{fmt(safe(df_today, 'ETF/機構'))}（機構參與提升）",
    ]

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
            if abs(diff) >= 0.1:
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

    img_pie = upload_to_r2(plot_btc_holder_pie(df_today, today))
    bubble = {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": img_pie,
            "size": "full",
            "aspectRatio": "1:1",
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
                    "backgroundColor": "#23272F",
                    "cornerRadius": "10px",
                    "paddingAll": "8px",       # 改小 padding
                    "margin": "none",         # 改無 margin
                    "contents": [
                        {"type": "text", "text": "【本日亮點】", "size": "md", "weight": "bold", "color": "#FFD600"},
                        *[
                            {"type": "text", "text": line, "size": "sm", "wrap": True, "color": "#F5FAFE", "margin": "sm"}
                            for line in highlight_lines
                        ]
                    ]
                },
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
