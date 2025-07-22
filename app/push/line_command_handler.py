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
import app.fetch_etf_daily as fetch_etf_daily

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
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "市值競賽榜", "text": "市值競賽榜"},
                            "style": "primary",
                            "margin": "md"
                        },
                    ]
                }
            ]
        }
    }

def parse_market_cap(symbol_str):
    if isinstance(symbol_str, str):
        symbol_str = symbol_str.replace('$', '').replace(',', '').strip()
        if 'T' in symbol_str:
            num = float(symbol_str.replace('T', '').strip()) * 10000  # 1T = 萬億 = 10000億
        elif 'B' in symbol_str:
            num = float(symbol_str.replace('B', '').strip()) * 10     # 1B = 10億
        elif 'M' in symbol_str:
            num = float(symbol_str.replace('M', '').strip()) / 100    # 1M = 0.01億
        else:
            try:
                num = float(symbol_str)
            except Exception:
                num = 0
        return num
    return 0.0

def parse_price(price_str):
    """ 解析價格字串，回傳數字 """
    if isinstance(price_str, str):
        try:
            return float(price_str.replace('$', '').replace(',', '').strip())
        except Exception:
            return None
    return None

def get_asset_competition_flex(today, df, img_url, market_cap_header):
    trophy = [f"{i+1:02d}" for i in range(len(df))]
    body_contents = [
        {
            "type": "text",
            "text": f"🌑 全球資產市值競賽 Top10（{today}）",
            "weight": "bold",
            "size": "lg",
            "color": "#F5FAFE",
            "wrap": True,
            "margin": "md"
        },
        {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "margin": "md",
            "contents": [
                {"type": "text", "text": "排", "color": "#C7D3E6", "size": "sm", "flex": 2, "align": "start"},
                {"type": "text", "text": "資產", "color": "#C7D3E6", "size": "sm", "flex": 6, "align": "end"},
                {"type": "text", "text": market_cap_header, "color": "#C7D3E6", "size": "sm", "align": "end", "flex": 8},
                # 價格 flex 調大到 10！
                {"type": "text", "text": "價格(美元)", "color": "#C7D3E6", "size": "sm", "align": "end", "flex": 9}
            ]
        }
    ]
    for i, row in df.iterrows():
        asset_code = row['ticker']
        market_cap_str = row['market_cap_display']
        price_str = row['price_display']
        body_contents.append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"{trophy[i]}", "size": "md", "color": "#FFD700" if i<3 else "#AAAAAA", "flex": 2, "align": "start"},
                {"type": "text", "text": asset_code, "weight": "bold", "color": "#F5FAFE", "flex": 6, "align": "end"},
                {"type": "text", "text": market_cap_str, "color": "#68A4FF", "flex": 8, "align": "end"},
                {"type": "text", "text": price_str, "color": "#FFA500", "flex": 9, "align": "end", "size": "sm"}
            ]
        })
    flex_message = {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": img_url,
            "size": "full",
            "aspectRatio": "2:1"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "backgroundColor": "#191E24",
            "contents": body_contents
        }
    }
    return flex_message

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

    print(f"[DEBUG] User ID: {user_id}, Message: {text}")  # 新增 debug

    if user_id != ADMIN_USER_ID:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("無權限"))
        return

    if text == SECRET_COMMAND:
        print("[DEBUG] SECRET_COMMAND triggered")  # 新增 debug
        try:
            fetch_etf_daily.fetch_and_save("BTC", days=5)
            fetch_etf_daily.fetch_and_save("ETH", days=5)
            reply_text = "✅ BTC 和 ETH 數據已成功更新到 Supabase！"
        except Exception as e:
            print(f"更新失敗：{e}")
            reply_text = "❌ 更新失敗，請稍後再試。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_text))
        return
    
    if text == "主選單":
        menu = get_main_menu_flex()
        line_bot_api.reply_message(event.reply_token, FlexSendMessage("主選單", menu))
        return

    # =========== ETF 查詢功能 ===========
    if text.lower().startswith("查詢"):
        tokens = text.split()
        symbol = tokens[1].upper() if len(tokens) > 1 else "BTC"
        days = int(tokens[2]) if len(tokens) > 2 else 16

        df_all = query_etf_flows_all(symbol)
        if df_all.empty:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("查無資料"))
            return

        target_date = get_latest_safe_etf_date(df_all)
        if target_date is None:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("查無可用結算日資料"))
            return

        df_target = df_all[df_all['date'] == pd.Timestamp(target_date)].copy()
        df_14d = get_recent_n_days_settled(df_all, target_date, n=days).copy()
        df_history = get_all_settled_until(df_all, target_date).copy()

        img_path = plot_etf_bar_chart(df_14d, symbol, days=days)
        if not os.path.exists(img_path):
            line_bot_api.reply_message(event.reply_token, TextSendMessage("ETF 圖檔生成失敗"))
            return

        api_key = os.getenv("IMGBB_API_KEY")
        if not api_key:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("imgbb API KEY 尚未設定"))
            return

        img_url = upload_imgbb(img_path)
        img_path_long = plot_etf_history_line_chart(df_history, symbol)
        img_url_long = upload_imgbb(img_path_long)

        df_target.loc[:, 'flow_usd'] = pd.to_numeric(df_target['flow_usd'], errors='coerce').fillna(0)
        total_today = df_target['flow_usd'].sum()
        etf_today_table = etf_flex_table_single_day(df_target)

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
            return "#00b300" if val > 0 else "#D50000" if val < 0 else "#F5FAFE"
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
                    "color": "#F5FAFE",
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

        # ==== 深色主題的 ETF 單日&歷史卡片 ====
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
                "backgroundColor": "#191E24",
                "contents": [
                    {"type": "text", "text": f"{symbol} ETF 資金流", "weight": "bold", "size": "xl", "color": "#F5FAFE"},
                    {"type": "text", "text": f"日期：{target_date.strftime('%Y-%m-%d')}", "size": "md", "color": "#F5FAFE"},
                    {"type": "text", "text": f"ETF 總淨流入/流出：{human_unit(total_today)}", "size": "md", "color": "#F5FAFE"},
                    {"type": "text", "text": "ETF 明細：", "weight": "bold", "size": "md", "margin": "md", "color": "#F5FAFE"},
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
                "backgroundColor": "#191E24",
                "contents": [
                    {"type": "text", "text": f"{symbol} ETF 全歷史資金流", "weight": "bold", "size": "xl", "color": "#F5FAFE"},
                    {"type": "text", "text": f"{df_history['date'].min().strftime('%Y-%m-%d')} ~ {df_history['date'].max().strftime('%Y-%m-%d')}", "size": "md", "color": "#F5FAFE"},
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

    # =========== 市值競賽榜功能 ===========
    if text.lower().startswith("市值競賽榜"):
        today = datetime.date.today().strftime('%Y-%m-%d')
        asset_list = fetch_global_asset_top10()
        df = asset_top10_to_df(asset_list, today)

        # 1. 資產代號
        df['ticker'] = df['name'].apply(lambda x: x.split()[-1].replace(")", ""))

        # 2. 市值（兆美元）
        df['market_cap_num'] = df['symbol'].apply(parse_market_cap)   # 用 market_cap_num 當主排序
        df['market_cap_display'] = df['market_cap_num'].apply(lambda x: f"{x/10000:.2f}" if x else "0.00")
        market_cap_header = "市值(兆美元)"

        # 3. 價格
        df['price_value'] = df['market_cap'].apply(parse_price)
        df['price_display'] = df['price_value'].apply(lambda x: f"{x:,.2f}" if x is not None else "-")

        # **主排序: 市值降冪，df_sorted = Top10順位**
        df_sorted = df.sort_values('market_cap_num', ascending=False).reset_index(drop=True)

        # bar chart 也用同樣的 df_sorted
        img_path = plot_asset_top10_bar_chart(df_sorted, today, unit_str="兆", unit_div=1e12)
        if not os.path.exists(img_path):
            line_bot_api.reply_message(event.reply_token, TextSendMessage("競賽榜圖檔生成失敗"))
            return

        img_url = upload_imgbb(img_path)
        # Flex 卡片資料也用 df_sorted
        flex_msg = get_asset_competition_flex(today, df_sorted, img_url, market_cap_header)
        line_bot_api.reply_message(event.reply_token, FlexSendMessage("全球資產競賽榜", flex_msg))
        return
