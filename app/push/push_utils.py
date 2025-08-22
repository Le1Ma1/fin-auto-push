import os
from linebot import LineBotApi
from linebot.models import FlexSendMessage, TextSendMessage
from app.db import query_active_whitelist

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

def push_flex_to_targets(flex_carousel, line_bot_api=None):
    if line_bot_api is None:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

    target_ids = query_active_whitelist()
    print(f"[DEBUG] 本次推播對象: {target_ids}")

    for to_id in target_ids:
        try:
            line_bot_api.push_message(to_id, FlexSendMessage("每日ETF+市值快報", flex_carousel))
        except Exception as e:
            print(f"推播失敗 {to_id}: {e}")

def push_text_to_targets(message: str, line_bot_api=None):
    """測試用：直接發送文字訊息給白名單用戶"""
    if line_bot_api is None:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

    target_ids = query_active_whitelist()
    print(f"[DEBUG] 本次文字推播對象: {target_ids}")

    for to_id in target_ids:
        try:
            line_bot_api.push_message(to_id, TextSendMessage(text=message))
        except Exception as e:
            print(f"文字推播失敗 {to_id}: {e}")
