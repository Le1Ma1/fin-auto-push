import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import app.fetcher.fetch_etf_daily as fetch_etf_daily
from app.push.flex_utils import get_full_flex_carousel
from app.push.push_utils import push_flex_to_targets

app = FastAPI()
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
ADMIN_USER_ID = os.getenv("LINE_ADMIN_USER_ID")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

SECRET_COMMAND = "!update_data"
SECRET_PUSH_TEST = "!test_push"
SECRET_FORCE_SYNC = "!force_sync"

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

    # 1. 補救抓ETF
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
    
    # 2. 測試推播
    if text == SECRET_PUSH_TEST:
        try:
            carousel = get_full_flex_carousel()
            push_flex_to_targets(carousel)
            reply_text = "✅ 已發送測試 Flex 推播！"
        except Exception as e:
            reply_text = f"❌ 測試推播失敗：{e}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_text))
        return

    # 3. 全自救（ETF + 資產榜一起補抓補入DB）
    if text == SECRET_FORCE_SYNC:
        print("[DEBUG] SECRET_COMMAND: 強制全同步 triggered")
        try:
            fetch_etf_daily.fetch_and_save("BTC", days=5)
            fetch_etf_daily.fetch_and_save("ETH", days=5)
            from app.fetcher.daily_asset_snapshot import daily_asset_snapshot
            daily_asset_snapshot()
            reply_text = "✅ 強制同步：BTC/ETH + 資產榜都已重抓並寫入雲端！"
        except Exception as e:
            print(f"同步失敗：{e}")
            reply_text = "❌ 強制同步失敗，請檢查日誌。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_text))
        return

    else:
        try:
            profile = line_bot_api.get_profile(event.source.user_id)
            user_name = profile.display_name
        except Exception as e:
            user_name = "(未知用戶)"
        print(f"[LINE用戶訊息] {user_name}: {user_id}\n訊息:\n{text}")