import os
import datetime
from dotenv import load_dotenv

# 這些 import 跟你的架構一致
from app.fetcher.asset_ranking import fetch_global_asset_top10
from app.pipeline.asset_ranking_df import asset_top10_to_df
from app.plot_chart import plot_asset_top10_bar_chart
from app.push.push_etf_chart import upload_imgbb
from linebot import LineBotApi
from linebot.models import TextSendMessage

load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_PUSH_USER_ID")  # 你想推播的 LINE 用戶 ID 或群組 ID

def main():
    today = datetime.date.today().strftime('%Y-%m-%d')
    asset_list = fetch_global_asset_top10()
    df = asset_top10_to_df(asset_list, today)
    img_path = plot_asset_top10_bar_chart(df, today)

    if not os.path.exists(img_path):
        print("❌ 圖檔產生失敗，無法推播！")
        return

    img_url = upload_imgbb(img_path)

    # 排行榜文字訊息
    msg = f"🌍 全球資產市值競賽榜 Top10（{today}）\n"
    for idx, row in df.sort_values("rank").iterrows():
        msg += f"{row['rank']}. {row['name']}（{row['symbol']}）：{row['market_cap']}\n"
    msg += f"\n[點我看圖表]({img_url})"

    # 推播到 LINE
    if CHANNEL_ACCESS_TOKEN and USER_ID:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(USER_ID, TextSendMessage(msg))
        print("✅ 已推播至 LINE 用戶/群組！")
    else:
        print("❗請確認 .env 內有 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_PUSH_USER_ID 設定")

if __name__ == "__main__":
    main()
