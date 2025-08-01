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
from app.pipeline.asset_ranking_df import asset_top10_to_df
from app.push.push_btc_holder import get_flex_bubble_btc_holder

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
            "aspectRatio": "2:1",
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

def get_flex_bubble_etf(symbol, df_all, target_date, days=14):
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

    # 歷史
    df_history = get_all_settled_until(df_all, target_date)
    img_hist = upload_to_r2(plot_etf_history_line_chart(df_history, symbol))
    total_flows_hist = df_history['total_flow_usd'].astype(float)
    nonzero_median_hist = safe_number(total_flows_hist[total_flows_hist != 0].median())
    mean_hist = safe_number(total_flows_hist.mean())
    max_in_hist = safe_number(total_flows_hist.max())
    max_out_hist = safe_number(total_flows_hist.min())
    max_in_date_hist = df_history.loc[total_flows_hist.idxmax(), 'date'].strftime('%Y-%m-%d') if not total_flows_hist.empty else ""
    max_out_date_hist = df_history.loc[total_flows_hist.idxmin(), 'date'].strftime('%Y-%m-%d') if not total_flows_hist.empty else ""

    bubble_hist = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": img_hist,
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
                {
                    "type": "text",
                    "text": f"最大單日淨流入：",
                    "size": "md",
                    "color": "#F5FAFE",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"{human_unit(max_in_hist)}（{max_in_date_hist}）",
                    "size": "md",
                    "color": "#00b300",
                    "weight": "bold",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"最大單日淨流出：",
                    "size": "md",
                    "color": "#F5FAFE",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"{human_unit(max_out_hist)}（{max_out_date_hist}）",
                    "size": "md",
                    "color": "#D50000",
                    "weight": "bold",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"中位數：",
                    "size": "md",
                    "color": "#F5FAFE",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"{human_unit(nonzero_median_hist)}",
                    "size": "md",
                    "color": "#00b300",
                    "weight": "bold",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"平均值：",
                    "size": "md",
                    "color": "#F5FAFE",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"{human_unit(mean_hist)}",
                    "size": "md",
                    "color": "#00b300",
                    "weight": "bold",
                    "margin": "sm"
                }
            ]
        }
    }
    return bubble_14d, bubble_hist

def get_full_flex_carousel():
    df_btc = query_etf_flows_all("BTC")
    target_btc_date = get_latest_safe_etf_date(df_btc)
    btc_bubble_14d, btc_bubble_hist = get_flex_bubble_etf("BTC", df_btc, target_btc_date)

    df_eth = query_etf_flows_all("ETH")
    target_eth_date = get_latest_safe_etf_date(df_eth)
    eth_bubble_14d, eth_bubble_hist = get_flex_bubble_etf("ETH", df_eth, target_eth_date)

    today = datetime.date.today().strftime('%Y-%m-%d')
    asset_list = fetch_global_asset_top10()
    df_asset = asset_top10_to_df(asset_list, today)
    df_asset['ticker'] = df_asset['name'].apply(lambda x: x.split()[-1].replace(")", ""))

    # 市值處理 function
    def en_unit_to_zh_and_fmt(s):
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

    import re
    def parse_market_cap_symbol(s):
        s = str(s).replace("$", "").replace(",", "").strip()
        match = re.match(r'([0-9.]+)\s*([TBM]?)', s)
        if not match:
            return 0
        num, unit = match.groups()
        unit_map = {"T": 1e12, "B": 1e9, "M": 1e6}
        num = float(num)
        mult = unit_map.get(unit, 1)
        return num * mult

    df_asset['market_cap_display'] = df_asset['symbol'].apply(en_unit_to_zh_and_fmt)
    df_asset['symbol_cap_num'] = df_asset['symbol'].apply(parse_market_cap_symbol)
    market_cap_header = "市值"

    df_asset['price_display'] = df_asset['market_cap_num'].apply(lambda x: f"{float(x):,.1f}" if pd.notnull(x) else "-")

    df_sorted = df_asset.sort_values('symbol_cap_num', ascending=False).reset_index(drop=True)

    img_asset = upload_to_r2(
        plot_asset_top10_bar_chart(
            df_sorted,
            today,
            unit_str="兆",
            unit_div=1e12
        )
    )
    flex_asset = get_asset_competition_flex(today, df_sorted, img_asset, market_cap_header)

    flex_btc_holder = get_flex_bubble_btc_holder(days=14)
    carousel = {
        "type": "carousel",
        "contents": [btc_bubble_14d, btc_bubble_hist, eth_bubble_14d, eth_bubble_hist, flex_asset, flex_btc_holder]
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
