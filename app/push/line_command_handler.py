import pandas as pd
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
import os
from dotenv import load_dotenv
from app.db import query_etf_flows_all
from app.plot_chart import plot_etf_bar_chart, plot_etf_history_line_chart
from app.push.push_etf_chart import upload_imgbb
from app.utils import (
    etf_flex_table_single_day,
    human_unit,
    fill_bar_chart_dates,
    get_latest_safe_etf_date,
    get_recent_n_days_settled,
    get_all_settled_until
)

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

        # ====== 安全結算日判斷 ======
        target_date = get_latest_safe_etf_date(df_all)
        if target_date is None:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("查無可用結算日資料"))
            return

        # -- 建立資料視窗 --
        df_target = df_all[df_all['date'] == pd.Timestamp(target_date)].copy()
        df_14d = get_recent_n_days_settled(df_all, target_date, n=days).copy()
        df_history = get_all_settled_until(df_all, target_date).copy()

        # ========== 圖表繪製 ==========
        img_path = plot_etf_bar_chart(df_14d, symbol, days=days)
        img_url = upload_imgbb(img_path)
        img_path_long = plot_etf_history_line_chart(df_history, symbol)
        img_url_long = upload_imgbb(img_path_long)

        # ========== 當日明細 ==========
        df_target.loc[:, 'flow_usd'] = pd.to_numeric(df_target['flow_usd'], errors='coerce').fillna(0)
        total_today = df_target['flow_usd'].sum()
        etf_today_table = etf_flex_table_single_day(df_target)

        # ========== 全歷史統計 ==========  
        total_flows_hist = df_history['total_flow_usd'].astype(float)
        def safe_number(val):
            if pd.isna(val) or val is None:
                return 0
            return val
        nonzero_median_hist = safe_number(total_flows_hist[total_flows_hist != 0].median())
        mean_hist = safe_number(total_flows_hist.mean())
        max_in_hist = safe_number(total_flows_hist.max())
        max_out_hist = safe_number(total_flows_hist.min())
        max_in_date_hist = df_history.loc[total_flows_hist.idxmax(), 'date'].strftime('%Y-%m-%d') if not total_flows_hist.empty else ""
        max_out_date_hist = df_history.loc[total_flows_hist.idxmin(), 'date'].strftime('%Y-%m-%d') if not total_flows_hist.empty else ""

        def font_color(val):
            return "#00b300" if val > 0 else "#D50000" if val < 0 else "#333333"

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
        history_items += format_stat("最大單日淨流入：", max_in_hist, max_in_date_hist)
        history_items += format_stat("最大單日淨流出：", max_out_hist, max_out_date_hist)
        history_items += format_stat("中位數：", nonzero_median_hist)
        history_items += format_stat("平均值：", mean_hist)

        # ========== Bubble/Flex 組件 ==========
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
                    {"type": "text", "text": f"{symbol} ETF 資金流", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": f"日期：{target_date.strftime('%Y-%m-%d')}", "size": "md"},
                    {"type": "text", "text": f"ETF 總淨流入/流出：{human_unit(total_today)}", "size": "md"},
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
                    {"type": "text", "text": f"{df_history['date'].min().strftime('%Y-%m-%d')} ~ {df_history['date'].max().strftime('%Y-%m-%d')}", "size": "md"},
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
