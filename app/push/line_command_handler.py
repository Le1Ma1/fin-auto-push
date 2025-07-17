import pandas as pd
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
import os
from dotenv import load_dotenv
from app.db import query_etf_flows, query_etf_flows_all
from app.plot_chart import plot_etf_bar_chart, plot_etf_history_line_chart
from app.push.push_etf_chart import upload_imgbb
from app.utils import etf_flex_table_single_day, human_unit, fill_bar_chart_dates

app = FastAPI()
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
ADMIN_USER_ID = os.getenv("LINE_ADMIN_USER_ID")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def get_main_menu_flex():
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "主選單", "weight": "bold", "size": "xl"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "查詢 BTC", "text": "查詢 BTC"},
                            "style": "primary",
                        },
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "查詢 ETH", "text": "查詢 ETH"},
                            "style": "primary",
                            "margin": "md"
                        },
                    ]
                }
            ]
        }
    }

@app.post("/callback")
async def callback(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    handler.handle(body.decode(), signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    if user_id != ADMIN_USER_ID:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("無權限"))
        return

    if text == "主選單":
        menu = get_main_menu_flex()
        line_bot_api.reply_message(event.reply_token, FlexSendMessage("主選單", menu))
        return

    if text.lower().startswith("查詢"):
        tokens = text.split()
        symbol = tokens[1].upper() if len(tokens) > 1 else "BTC"
        days = int(tokens[2]) if len(tokens) > 2 else 14

        df_all = query_etf_flows_all(symbol)
        if df_all.empty:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("查無資料"))
            return

        df_bar_raw = df_all[df_all['date'] >= df_all['date'].max() - pd.Timedelta(days=days*2)]
        df_bar = fill_bar_chart_dates(df_bar_raw, days=days)
        df_bar = df_bar[df_bar['date'].dt.weekday < 5]  # 只要週一到週五

        # 圖片
        img_path = plot_etf_bar_chart(df_bar, symbol, days=days)
        img_url = upload_imgbb(img_path)
        img_path_long = plot_etf_history_line_chart(df_all, symbol)
        img_url_long = upload_imgbb(img_path_long)

        today = str(df_bar['date'].max())
        df_bar['flow_usd'] = pd.to_numeric(df_bar['flow_usd'], errors='coerce').fillna(0)
        df_today = df_bar[df_bar['date'] == df_bar['date'].max()]
        total_today = df_today['flow_usd'].sum()
        etf_today_table = etf_flex_table_single_day(df_bar)

        # ===== 新增統計區塊與顏色 =====
        total_flows = df_all['total_flow_usd'].astype(float)
        def safe_number(val):
            if pd.isna(val) or val is None:
                return 0
            return val
        nonzero_median = safe_number(total_flows[total_flows != 0].median())
        mean = safe_number(total_flows.mean())
        max_in = safe_number(total_flows.max())
        max_out = safe_number(total_flows.min())

        # 發生日期
        max_in_date = df_all.loc[total_flows.idxmax(), 'date'].strftime('%Y-%m-%d') if not total_flows.empty else ""
        max_out_date = df_all.loc[total_flows.idxmin(), 'date'].strftime('%Y-%m-%d') if not total_flows.empty else ""

        def font_color(val):
            return "#00b300" if val > 0 else "#D50000" if val < 0 else "#333333"

        # 格式化數值 + 日期
        def format_stat(title, value, date=None):
            color = font_color(value)
            text = f"{human_unit(value)}"
            if date:
                text = f"{text}（{date}）"
            return [
                {
                    "type": "text",
                    "text": title,
                    "size": "sm",
                    "weight": "regular",
                    "color": "#333333",
                    "margin": "md",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": text,
                    "size": "sm",
                    "weight": "bold",
                    "color": color,
                    "margin": "sm",
                    "wrap": True
                }
            ]

        history_items = []
        history_items += format_stat("最大單日淨流入：", max_in, max_in_date)
        history_items += format_stat("最大單日淨流出：", max_out, max_out_date)
        history_items += format_stat("中位數：", nonzero_median)
        history_items += format_stat("平均值：", mean)

        flex_short = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": img_url,
                "size": "full",
                "aspectRatio": "2:1"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"{symbol} ETF 今日資金流", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": f"日期：{today}", "size": "md"},
                    {"type": "text", "text": f"今日 ETF 總淨流入/流出：{human_unit(total_today)}", "size": "md"},
                    {"type": "text", "text": "ETF 明細：", "weight": "bold", "size": "md", "margin": "md"},
                    *etf_today_table
                ]
            }
        }
        flex_long = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": img_url_long,
                "size": "full",
                "aspectRatio": "2:1"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"{symbol} ETF 全歷史資金流", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": f"{df_all['date'].min().strftime('%Y-%m-%d')} ~ {df_all['date'].max().strftime('%Y-%m-%d')}", "size": "md"},
                    *history_items
                ]
            }
        }
        carousel = {
            "type": "carousel",
            "contents": [flex_short, flex_long]
        }
        msg = FlexSendMessage(alt_text="ETF 走勢圖", contents=carousel)
        line_bot_api.reply_message(event.reply_token, msg)
        return

    line_bot_api.reply_message(event.reply_token, TextSendMessage("請使用主選單或輸入：查詢 BTC/ETH [天數]"))
