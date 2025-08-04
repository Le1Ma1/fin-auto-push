import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import app.fetcher.fetch_etf_daily as fetch_etf_daily
from app.push.flex_utils import get_full_flex_carousel, get_plan_flex_bubble, get_pro_plan_carousel, get_elite_carousels, get_flex_bubble_fear_greed, get_flex_bubble_exchange_balance, get_flex_bubble_funding_rate, get_flex_bubble_whale_alert
from app.push.push_utils import push_flex_to_targets
from app.btc_holder_distribution import fetch_btc_holder_distribution
from app.btc_holder_distribution_df import btc_holder_df_to_db
from app.db import upsert_btc_holder_distribution
from app.fetcher.fetch_fear_greed import fetch_and_save_fear_greed
from app.fetcher.fetch_exchange_balance import fetch_and_save_exchange_balance
from app.fetcher.fetch_funding_rate import fetch_and_save_funding_rate
from app.fetcher.fetch_whale_alert import fetch_and_save_whale_alert

app = FastAPI()
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
ADMIN_USER_ID = os.getenv("LINE_ADMIN_USER_ID")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

SECRET_COMMANDS = {
    "更新ETF": "!update_data",
    "測試推播": "!test_push",
    "強制全同步": "!force_sync",
    "持幣分布上傳": "!test_holder_upsert",
    "LTH 歷史補抓": "!sync_lth_history",
    # 新增補抓指令
    "補抓恐懼貪婪全歷史": "!sync_fear_greed",
    "補抓交易所餘額全歷史": "!sync_exchange_balance",
    "補抓 FundingRate 全歷史": "!sync_funding_rate",
    "補抓 Whale Alert": "!sync_whale_alert",
    # 新增 Bubble 測試推播指令
    "測試 Pro 推播": "!test_pro_push",
    "測試 Elite 推播": "!test_elite_push"
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

    print(f"[DEBUG] User ID: {user_id}, Message: {text}")

    # 1. 任何人都可用「方案介紹」
    if text in ["/方案介紹", "方案介紹"]:
        flex_bubble = get_plan_flex_bubble()
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage("訂閱方案介紹", flex_bubble)
        )
        return

    # 2. 僅允許管理員使用秘密指令（! 開頭）
    if text.startswith("!"):
        if user_id == ADMIN_USER_ID:
            # ---- 新增 Bubble 全歷史補抓 ----
            if text == SECRET_COMMANDS["補抓恐懼貪婪全歷史"]:
                fetch_and_save_fear_greed(days=2000)
                reply = "✅ 恐懼與貪婪指數全歷史已抓取！"
            elif text == SECRET_COMMANDS["補抓交易所餘額全歷史"]:
                fetch_and_save_exchange_balance(days=2000)
                reply = "✅ 交易所餘額全歷史已抓取！"
            elif text == SECRET_COMMANDS["補抓 FundingRate 全歷史"]:
                fetch_and_save_funding_rate(days=2000)
                reply = "✅ Funding Rate 全歷史已抓取！"
            elif text == SECRET_COMMANDS["補抓 Whale Alert"]:
                fetch_and_save_whale_alert()  # 只能補抓近24小時
                reply = "✅ Whale Alert 最新24h已抓取！"
            # ---- 新增 Bubble 測試推播 ----
            elif text == SECRET_COMMANDS["測試 Pro 推播"]:
                carousel = get_pro_plan_carousel()
                push_flex_to_targets(carousel)
                reply = "✅ Pro 方案推播已測試送出"
            elif text == SECRET_COMMANDS["測試 Elite 推播"]:
                carousels = get_elite_carousels()
                for carousel in carousels:
                    push_flex_to_targets(carousel)
                reply = "✅ Elite 方案推播已測試送出"
            # ---- 原有管理指令保留（如 ETF、LTH等） ----
            elif text == SECRET_COMMAND:
                # ...原本流程
                reply = "..."
            # ... 其它略
            else:
                reply = None

            if reply:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))
            return
        else:
            # 非管理員靜音
            return
