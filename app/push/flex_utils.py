import datetime
import pandas as pd
from app.db import query_etf_flows_all
from app.plot_chart import plot_etf_bar_chart, plot_etf_history_line_chart, plot_asset_top10_bar_chart
from app.push.push_etf_chart import upload_to_r2
from app.utils import (
    etf_flex_table_single_day,
    human_unit,
    get_latest_safe_etf_date,
    get_recent_n_days_settled,
    get_all_settled_until
)
from app.fetcher.asset_ranking import fetch_global_asset_top10
from app.pipeline.asset_ranking_df import asset_top10_to_df, parse_market_cap_symbol
from app.push.push_btc_holder import get_flex_bubble_btc_holder

# ---- 防呆包裝，每張 bubble 報錯不會中斷主流程 ----
def safe_bubble(bubble_func, *args, **kwargs):
    try:
        print(f"[DEBUG] 開始產生 {bubble_func.__name__}")
        result = bubble_func(*args, **kwargs)
        print(f"[DEBUG] {bubble_func.__name__} 完成")
        return result
    except Exception as e:
        print(f"[ERROR] {bubble_func.__name__} 產生失敗：{e}")
        return None

def en_unit_to_zh_and_fmt(s):
    """市值字串轉中文單位（for display）"""
    s = str(s).replace("$", "").strip()
    import re
    match = re.match(r'([0-9.]+)\s*([TBM]?)', s)
    if match:
        num, unit = match.groups()
        try:
            num_fmt = f"{float(num):,.1f}"
        except:
            num_fmt = num
        unit_map = {"T": "兆", "B": "億", "M": "百萬"}
        zh_unit = unit_map.get(unit, unit)
        return f"{num_fmt}{zh_unit}"
    else:
        return s

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
                {"type": "text", "text": f'{market_cap_header}(美元)', "color": "#C7D3E6", "size": "sm", "align": "end", "flex": 8},
                {"type": "text", "text": "價格(美元)", "color": "#C7D3E6", "size": "sm", "align": "end", "flex": 9}
            ]
        }
    ]
    
    for i, row in df.iterrows():
        asset_code = row.get('short_name', row.get('name', '-'))
        market_cap_str = row.get('market_cap_zh', '-')    # 只顯示「x.x兆」
        price_str = row.get('price_display', '-')
        body_contents.append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"{trophy[i]}", "size": "md", "color": "#FFD700" if i < 3 else "#AAAAAA", "flex": 2, "align": "start"},
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
            "aspectRatio": "12.3:6.6",
            "aspectMode": "fit"
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

def safe_number(val):
    if pd.isna(val) or val is None:
        return 0
    return val

def get_flex_bubble_etf(symbol, df_all, target_date, days=30):
    # 單日
    df_day = df_all[df_all['date'] == pd.Timestamp(target_date)].copy()
    total_today = df_day['flow_usd'].sum()
    etf_today_table = etf_flex_table_single_day(df_day)
    df_14d = get_recent_n_days_settled(df_all, target_date, n=days)
    img_14d = upload_to_r2(plot_etf_bar_chart(df_14d, symbol, days=days))

    bubble_14d = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": img_14d,
            "size": "full",
            "aspectRatio": "12.1:7"
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

    # 歷史
    df_history = get_all_settled_until(df_all, target_date)
    img_hist = upload_to_r2(plot_etf_history_line_chart(df_history, symbol))
    total_flows_hist = df_history['total_flow_usd'].astype(float)
    nonzero_median_hist = safe_number(total_flows_hist[total_flows_hist != 0].median())
    mean_hist = safe_number(total_flows_hist.mean())
    max_in_hist = safe_number(total_flows_hist.max())
    max_out_hist = safe_number(total_flows_hist.min())
    max_in_date_hist = df_history.loc[total_flows_hist.idxmax(), 'date'].strftime('%Y-%m-%d') if not df_history.empty else ""
    max_out_date_hist = df_history.loc[total_flows_hist.idxmin(), 'date'].strftime('%Y-%m-%d') if not df_history.empty else ""

    bubble_hist = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": img_hist,
            "size": "full",
            "aspectRatio": "12.1:6"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "contents": [
                {"type": "text", "text": f"{symbol} ETF 全歷史資金流", "weight": "bold", "size": "xl", "color": "#F5FAFE"},
                {"type": "text", "text": f"{df_history['date'].min().strftime('%Y-%m-%d')} ~ {df_history['date'].max().strftime('%Y-%m-%d')}", "size": "md", "color": "#F5FAFE"},
                {"type": "text", "text": f"最大單日淨流入：", "size": "md", "color": "#F5FAFE", "margin": "md"},
                {"type": "text", "text": f"{human_unit(max_in_hist)}（{max_in_date_hist}）", "size": "md", "color": "#00b300", "weight": "bold", "margin": "sm"},
                {"type": "text", "text": f"最大單日淨流出：", "size": "md", "color": "#F5FAFE", "margin": "md"},
                {"type": "text", "text": f"{human_unit(max_out_hist)}（{max_out_date_hist}）", "size": "md", "color": "#D50000", "weight": "bold", "margin": "sm"},
                {"type": "text", "text": f"中位數：", "size": "md", "color": "#F5FAFE", "margin": "md"},
                {"type": "text", "text": f"{human_unit(nonzero_median_hist)}", "size": "md", "color": "#00b300", "weight": "bold", "margin": "sm"},
                {"type": "text", "text": f"平均值：", "size": "md", "color": "#F5FAFE", "margin": "md"},
                {"type": "text", "text": f"{human_unit(mean_hist)}", "size": "md", "color": "#00b300", "weight": "bold", "margin": "sm"}
            ]
        }
    }
    return bubble_14d, bubble_hist

def get_full_flex_carousel():
    print("========== 產生 Flex Carousel ==========")
    # BTC ETF
    df_btc = query_etf_flows_all("BTC")
    df_btc['date'] = pd.to_datetime(df_btc['date'])
    target_btc_date = df_btc['date'].max()
    btc_bubble_14d, btc_bubble_hist = (None, None)
    try:
        btc_bubble_14d, btc_bubble_hist = get_flex_bubble_etf("BTC", df_btc, target_btc_date)
        print("[DEBUG] btc_bubble_14d/btc_bubble_hist 完成")
    except Exception as e:
        print(f"[ERROR] btc ETF bubble 失敗：{e}")

    # ETH ETF
    df_eth = query_etf_flows_all("ETH")
    df_eth['date'] = pd.to_datetime(df_eth['date'])              # <== 這行保證正確型別
    target_eth_date = df_eth['date'].max()
    print("[DEBUG] ETH 最新日期:", target_eth_date)
    
    eth_bubble_14d, eth_bubble_hist = (None, None)
    try:
        eth_bubble_14d, eth_bubble_hist = get_flex_bubble_etf("ETH", df_eth, target_eth_date)
        print("[DEBUG] eth_bubble_14d/eth_bubble_hist 完成")
    except Exception as e:
        print(f"[ERROR] eth ETF bubble 失敗：{e}")

    # ------ 市值 Top10 FLEX，這裡保證你資料格式正確 ------
    flex_asset = None
    try:
        today = datetime.date.today().strftime('%Y-%m-%d')
        asset_list = fetch_global_asset_top10()
        df_asset = asset_top10_to_df(asset_list, today)
        print(df_asset[['name', 'symbol', 'market_cap', 'market_cap_num']])

        def parse_float_safe(x):
            try:
                if isinstance(x, str):
                    x = x.replace("$", "").replace(",", "").strip()
                return float(x)
            except Exception:
                return float('nan')

        df_asset['price_display'] = df_asset['market_cap'].apply(
            lambda x: f"{parse_float_safe(x):,.1f}" if pd.notnull(x) else "-"
        )

        def symbol_to_zh_t(val):
            import re
            if not isinstance(val, str):
                return "-"
            match = re.match(r'\$?([\d.]+)\s*T', val)
            if match:
                num = float(match.group(1))
                return f"{num:.1f}兆"
            return val

        df_asset['short_name'] = df_asset['name'].apply(
            lambda x: x.strip().split()[-1] if isinstance(x, str) and x.strip() else x
        )
        df_asset['market_cap_zh'] = df_asset['symbol'].apply(symbol_to_zh_t)
        # ----------------------------------

        # 3. 排序、畫圖
        df_sorted = df_asset.sort_values('market_cap_num', ascending=False).reset_index(drop=True)
        img_asset = upload_to_r2(
            plot_asset_top10_bar_chart(
                df_sorted,
                today,
                unit_str="兆",
                unit_div=1e12
            )
        )
        market_cap_header = "市值"
        # 4. Flex Bubble 組裝，這裡 asset_name 要用 name，market_cap_str 用 symbol
        flex_asset = get_asset_competition_flex(today, df_sorted, img_asset, market_cap_header)
        print("[DEBUG] flex_asset 完成")
    except Exception as e:
        print(f"[ERROR] flex_asset 失敗：{e}")

    # BTC 六大類持幣
    flex_btc_holder = safe_bubble(get_flex_bubble_btc_holder, days=14)

    # 組裝 carousel
    bubbles = [
        btc_bubble_14d,
        btc_bubble_hist,
        eth_bubble_14d,
        eth_bubble_hist,
        flex_asset,
        flex_btc_holder,
        # ...其它 future bubble
    ]
    bubbles = [b for b in bubbles if b is not None]
    print(f"[INFO] 成功產生 {len(bubbles)} 張 bubble")
    carousel = {
        "type": "carousel",
        "contents": bubbles
    }
    return carousel

def get_plan_flex_bubble():
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "paddingAll": "24px",
            "contents": [
                # 標題
                {
                    "type": "text",
                    "text": "訂閱方案介紹",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#F5FAFE",
                    "align": "center"
                },
                # Pro 進階版
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xl",
                    "spacing": "sm",
                    "paddingAll": "18px",
                    "backgroundColor": "#23272F",
                    "cornerRadius": "18px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "進階版 Pro",
                            "size": "lg",
                            "weight": "bold",
                            "color": "#34d399"
                        },
                        {
                            "type": "text",
                            "text": "每月 NT$199｜年繳 NT$1,999",
                            "size": "md",
                            "color": "#A3E635",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": (
                                "• BTC/ETH/ETF 六分類\n"
                                "• 持幣結構圖表\n"
                                "• 全球資產排行\n"
                                "• 獨家精華摘要\n"
                                "🎁 更多數據將免費解鎖"
                            ),
                            "wrap": True,
                            "color": "#F5FAFE",
                            "margin": "md"
                        }
                    ]
                },
                # 分隔線
                {"type": "separator", "margin": "xl"},
                # Elite 專業版
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xl",
                    "spacing": "sm",
                    "paddingAll": "18px",
                    "backgroundColor": "#23272F",
                    "cornerRadius": "18px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "專業版 Elite（敬請期待）",
                            "size": "lg",
                            "weight": "bold",
                            "color": "#60a5fa"
                        },
                        {
                            "type": "text",
                            "text": "每月 NT$399｜年繳 NT$3,999",
                            "size": "md",
                            "color": "#A3E635",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": (
                                "即將開放：\n"
                                "• 巨鯨動向追蹤\n"
                                "• ETF 深度數據\n"
                                "• 自訂智能推播\n"
                                "• 多幣種/多維查詢"
                            ),
                            "wrap": True,
                            "color": "#A5B4FC",
                            "margin": "md"
                        }
                    ]
                },
                # 按鈕區塊（只保留一個主升級按鈕，次按鈕亮色＋白字）
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xl",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "我要升級",
                                "uri": "https://liff.line.me/2007745575-JPOMYKYn"
                            },
                            "style": "primary",
                            "color": "#F59E42",          # 亮橘
                            "height": "sm",
                            "margin": "none",
                            "gravity": "center",
                            "cornerRadius": "10px"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "官網詳情",
                                "uri": "https://leimaitech.com"
                            },
                            "style": "secondary",
                            "color": "#50545A",         # 亮灰色（主題色基礎上提亮2-3階）
                            "height": "sm",
                            "margin": "none",
                            "gravity": "center",
                            "cornerRadius": "10px",
                            "textColor": "#F5FAFE"      # Flex支援時會強制白字
                        }
                    ]
                }
            ]
        }
    }