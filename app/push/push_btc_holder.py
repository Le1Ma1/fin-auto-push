from app.db import query_btc_holder_distribution
from app.plot_chart_btc_holder import plot_btc_holder_pie, plot_btc_holder_stacked
from app.push.push_etf_chart import upload_imgbb

def get_flex_bubble_btc_holder(days=14):
    df_hist = query_btc_holder_distribution(days=days)
    today = df_hist['date'].max().strftime("%Y-%m-%d")
    df_today = df_hist[df_hist['date'] == df_hist['date'].max()]
    img_pie = upload_imgbb(plot_btc_holder_pie(df_today, today))
    img_stacked = upload_imgbb(plot_btc_holder_stacked(df_hist))

    total = int(df_today['btc_count'].sum())
    highlight = df_today.loc[df_today['btc_count'].idxmax()]
    msg = f"六大類總持幣 {total:,} BTC\n最大分類：{highlight['category']} {int(highlight['btc_count']):,} BTC（{highlight['percent']}%）"

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
                {"type": "text", "text": f"日期：{today}", "size": "md", "color": "#F5FAFE"},
                {"type": "text", "text": msg, "size": "md", "color": "#68A4FF"},
                {"type": "image", "url": img_stacked, "size": "full", "aspectRatio": "2:1", "margin": "md"}
            ]
        }
    }
    return bubble
