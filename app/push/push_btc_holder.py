from app.db import query_btc_holder_distribution
from app.plot_chart_btc_holder import plot_btc_holder_pie
from app.push.push_etf_chart import upload_to_r2
from app.utils import generate_btc_holder_highlight

def get_flex_bubble_btc_holder(days=1):
    df_hist = query_btc_holder_distribution(days=days)
    today = df_hist['date'].max().strftime("%Y-%m-%d")
    df_today = df_hist[df_hist['date'] == df_hist['date'].max()]
    # 嘗試取得昨日資料（假設有 2 天資料）
    if len(df_hist['date'].unique()) >= 2:
        yesterday = sorted(df_hist['date'].unique())[-2]
        df_yesterday = df_hist[df_hist['date'] == yesterday]
    else:
        df_yesterday = None
    # 產生亮點摘要
    highlight_text = generate_btc_holder_highlight(df_today, df_yesterday)
    img_pie = upload_to_r2(plot_btc_holder_pie(df_today, today))

    bubble = {
        "type": "bubble",
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
                {"type": "text", "text": f"日期：{today}", "size": "md", "color": "#F5FAFE"},
                # 新增 highlight 亮點區
                {"type": "text", "text": f"【本日亮點】\n{highlight_text}", "size": "sm", "color": "#F5FAFE", "wrap": True, "margin": "md"},
                # 你的分類說明區也可以加在這
            ]
        }
    }
    return bubble

