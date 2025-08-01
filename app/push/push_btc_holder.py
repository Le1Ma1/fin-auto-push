from app.db import query_btc_holder_distribution
from app.plot_chart_btc_holder import plot_btc_holder_pie
from app.push.push_etf_chart import upload_to_r2

def get_flex_bubble_btc_holder(days=1):
    df_hist = query_btc_holder_distribution(days=days)
    today = df_hist['date'].max().strftime("%Y-%m-%d")
    df_today = df_hist[df_hist['date'] == df_hist['date'].max()]
    img_pie = upload_to_r2(plot_btc_holder_pie(df_today, today))

    bubble = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": img_pie,
            "size": "full",
            "aspectRatio": "1:1"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "contents": [
                {"type": "text", "text": "BTC 六大類持幣分布", "weight": "bold", "size": "xl", "color": "#F5FAFE"},
                {"type": "text", "text": f"日期：{today}", "size": "md", "color": "#F5FAFE"}
            ]
        }
    }
    return bubble
