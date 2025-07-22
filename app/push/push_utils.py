import os
from linebot import LineBotApi
from linebot.models import FlexSendMessage

PUSH_GROUP_IDS = os.getenv('PUSH_GROUP_IDS', "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
TARGET_IDS = [i.strip() for i in PUSH_GROUP_IDS.split(",") if i.strip()]

def push_flex_to_targets(flex_carousel, line_bot_api=None):
    if line_bot_api is None:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    for to_id in TARGET_IDS:
        try:
            line_bot_api.push_message(to_id, FlexSendMessage("每日ETF+市值快報", flex_carousel))
        except Exception as e:
            print(f"推播失敗 {to_id}: {e}")
