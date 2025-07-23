import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
from app.db import query_etf_flows_all
from app.plot_chart import plot_etf_bar_chart, plot_etf_history_line_chart, plot_asset_top10_bar_chart
from app.push.push_etf_chart import upload_imgbb
from app.utils import (
    etf_flex_table_single_day,
    human_unit,
    fill_bar_chart_dates,
    get_latest_safe_etf_date,
    get_recent_n_days_settled,
    get_all_settled_until,
    get_ch_unit_and_div
)
from app.fetcher.asset_ranking import fetch_global_asset_top10
from app.pipeline.asset_ranking_df import asset_top10_to_df
import app.fetcher.fetch_etf_daily as fetch_etf_daily

app = FastAPI()
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
ADMIN_USER_ID = os.getenv("LINE_ADMIN_USER_ID")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
SECRET_COMMAND = "!update_data"

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

    print(f"[DEBUG] User ID: {user_id}, Message: {text}")

    if user_id != ADMIN_USER_ID:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("無權限"))
        return


    if text == SECRET_COMMAND:
        print("[DEBUG] SECRET_COMMAND triggered")
        try:
            fetch_etf_daily.fetch_and_save("BTC", days=5)
            fetch_etf_daily.fetch_and_save("ETH", days=5)
            reply_text = "✅ BTC 和 ETH 數據已成功更新到 Supabase！"
        except Exception as e:
            print(f"更新失敗：{e}")
            reply_text = "❌ 更新失敗，請稍後再試。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_text))
        return
