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
            "aspectRatio": "12.3:6",
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
    max_in_date_hist = df_history.loc[total_flows_hist.idxmax(), 'date'].strftime('%Y-%m-%d') if not total_flows_hist.empty else ""
    max_out_date_hist = df_history.loc[total_flows_hist.idxmin(), 'date'].strftime('%Y-%m-%d') if not total_flows_hist.empty else ""

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

def get_flex_bubble_fear_greed():
    from app.db import supabase  # 你的 supabase 物件
    import pandas as pd
    # 查詢 14 日資料
    rows = supabase.table("fear_greed_index").select("*").order("date", desc=True).limit(14).execute().data
    if not rows:
        # fallback or placeholder
        fg_score, fg_level, fg_yesterday, fg_high, fg_low, fg_tips = 0, "-", 0, 0, 0, "暫無資料"
        fg_img_url = "https://your-cdn.com/feargreed-placeholder.png"
    else:
        df = pd.DataFrame(rows).sort_values("date")
        fg_score = int(df.iloc[-1]["score"])
        fg_level = df.iloc[-1]["level"]
        fg_yesterday = int(df.iloc[-2]["score"]) if len(df) >= 2 else "-"
        fg_high = int(df["score"].max())
        fg_low = int(df["score"].min())
        # Tips 可根據極端自動產生
        fg_tips = "極端恐懼，留意抄底機會！" if fg_score < 25 else ("極端貪婪，謹防高位震盪！" if fg_score > 75 else "情緒中性，謹慎操作")
        # 畫圖上傳
        from app.plot_chart_fear_greed import plot_fear_greed_line_chart, upload_to_r2
        fg_img_path = plot_fear_greed_line_chart(df)
        fg_img_url = upload_to_r2(fg_img_path)
    return {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": fg_img_url,
            "size": "full",
            "aspectRatio": "12.1:7",
            "aspectMode": "fit"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "contents": [
                {"type": "text", "text": f"恐懼與貪婪指數 {fg_score}", "size": "xl", "weight": "bold", "color": "#F5FAFE"},
                {"type": "text", "text": f"今日情緒：{fg_level}", "size": "md", "color": "#A3E635", "weight": "bold"},
                {"type": "text", "text": f"昨日：{fg_yesterday} | 14日高：{fg_high} 低：{fg_low}", "size": "sm", "color": "#C7D3E6"},
                {"type": "text", "text": fg_tips, "size": "sm", "color": "#FBBF24"}
            ]
        }
    }

def get_flex_bubble_exchange_balance():
    from app.db import supabase
    import pandas as pd
    # 取 14 日資料
    rows = supabase.table("exchange_btc_balance").select("*").order("date", desc=True).limit(14*5).execute().data  # 取多一點，方便 groupby
    if not rows:
        exb_img_url = "https://your-cdn.com/exb-placeholder.png"
        exb_max_in = {"exchange": "-", "amt": "-"}
        exb_max_out = {"exchange": "-", "amt": "-"}
        exb_top3_in_sum = "-"
    else:
        df = pd.DataFrame(rows)
        # 將資料整理成每天每所的餘額
        df = df.sort_values(["date", "exchange"])
        # 計算今日/昨日流入流出
        latest_date = df["date"].max()
        prev_date = df["date"].unique()[-2] if len(df["date"].unique()) >= 2 else None
        # 合併今日與昨日，計算餘額變化
        today_df = df[df["date"] == latest_date].set_index("exchange")
        prev_df = df[df["date"] == prev_date].set_index("exchange") if prev_date else None
        if prev_df is not None:
            merged = today_df.join(prev_df, lsuffix="_today", rsuffix="_prev", how="left").fillna(0)
            merged["change"] = merged["btc_balance_today"] - merged["btc_balance_prev"]
            # 最大流入
            max_in = merged["change"].idxmax()
            exb_max_in = {"exchange": max_in, "amt": f"{merged.loc[max_in]['change']:.0f}"}
            # 最大流出
            max_out = merged["change"].idxmin()
            exb_max_out = {"exchange": max_out, "amt": f"{merged.loc[max_out]['change']:.0f}"}
            # Top3合計流入
            exb_top3_in_sum = f"{merged['change'].sort_values(ascending=False)[:3].sum():.0f}"
        else:
            exb_max_in = {"exchange": "-", "amt": "-"}
            exb_max_out = {"exchange": "-", "amt": "-"}
            exb_top3_in_sum = "-"
        # 畫圖
        from app.plot_chart_exchange_balance import plot_exchange_balance_chart, upload_to_r2
        exb_img_path = plot_exchange_balance_chart(df)
        exb_img_url = upload_to_r2(exb_img_path)
    return {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": exb_img_url,
            "size": "full",
            "aspectRatio": "12.1:7",
            "aspectMode": "fit"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "contents": [
                {"type": "text", "text": "BTC 交易所持幣流向", "size": "xl", "weight": "bold", "color": "#F5FAFE"},
                {"type": "text", "text": f"最大流入：{exb_max_in['exchange']} {exb_max_in['amt']} BTC", "size": "sm", "color": "#A3E635"},
                {"type": "text", "text": f"最大流出：{exb_max_out['exchange']} {exb_max_out['amt']} BTC", "size": "sm", "color": "#FA5252"},
                {"type": "text", "text": f"Top3合計流入：{exb_top3_in_sum} BTC", "size": "sm", "color": "#C7D3E6"}
            ]
        }
    }

def get_flex_bubble_funding_rate():
    from app.db import supabase
    import pandas as pd
    # 取 14 日資料
    rows = supabase.table("funding_rate").select("*").order("date", desc=True).limit(14*5).execute().data
    if not rows:
        fr_img_url = "https://your-cdn.com/funding-placeholder.png"
        fr_max, fr_min, fr_avg, fr_alert, fr_tips = 0, 0, 0, False, "暫無資料"
    else:
        df = pd.DataFrame(rows)
        # 對不同交易所平均
        group = df.groupby("date")["rate"].mean().tail(14)
        fr_max = group.max()
        fr_min = group.min()
        fr_avg = group.mean()
        fr_alert = (abs(fr_max) > 0.01) or (abs(fr_min) < -0.01)  # 自行定義極端標準
        fr_tips = "合約槓桿極端，注意爆倉風險" if fr_alert else "市場槓桿中性"
        # 畫圖
        from app.plot_chart_funding_rate import plot_funding_rate_chart, upload_to_r2
        fr_img_path = plot_funding_rate_chart(group)
        fr_img_url = upload_to_r2(fr_img_path)
    return {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": fr_img_url,
            "size": "full",
            "aspectRatio": "12.1:7",
            "aspectMode": "fit"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "contents": [
                {"type": "text", "text": "BTC Funding Rate", "size": "xl", "weight": "bold", "color": "#F5FAFE"},
                {"type": "text", "text": f"今日最大：{fr_max:.3%} 最小：{fr_min:.3%}", "size": "sm", "color": "#FBBF24" if fr_alert else "#A3E635"},
                {"type": "text", "text": f"平均：{fr_avg:.3%}", "size": "sm", "color": "#C7D3E6"},
                {"type": "text", "text": fr_tips, "size": "sm", "color": "#FA5252" if fr_alert else "#F5FAFE"}
            ]
        }
    }

def get_flex_bubble_whale_alert():
    from app.db import supabase
    import pandas as pd
    # 取近一天資料
    today = pd.Timestamp.today().strftime('%Y-%m-%d')
    rows = supabase.table("whale_alert").select("*").eq("date", today).execute().data
    if not rows:
        wa_img_url = "https://your-cdn.com/whale-placeholder.png"
        wa_max = {"from": "-", "to": "-", "amt": "-"}
        wa_2nd = {"from": "-", "to": "-", "amt": "-"}
        wa_total_count, wa_total_amt = 0, 0
    else:
        df = pd.DataFrame(rows)
        df = df.sort_values("amount", ascending=False)
        wa_max = {
            "from": df.iloc[0]["from_address"],
            "to": df.iloc[0]["to_address"],
            "amt": f"{df.iloc[0]['amount']:.0f}"
        }
        wa_2nd = {
            "from": df.iloc[1]["from_address"] if len(df) > 1 else "-",
            "to": df.iloc[1]["to_address"] if len(df) > 1 else "-",
            "amt": f"{df.iloc[1]['amount']:.0f}" if len(df) > 1 else "-"
        }
        wa_total_count = len(df)
        wa_total_amt = f"{df['amount'].sum():.0f}"
        # 畫圖
        from app.plot_chart_whale_alert import plot_whale_alert_chart, upload_to_r2
        wa_img_path = plot_whale_alert_chart(df)
        wa_img_url = upload_to_r2(wa_img_path)
    return {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": wa_img_url,
            "size": "full",
            "aspectRatio": "12.1:7",
            "aspectMode": "fit"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#191E24",
            "contents": [
                {"type": "text", "text": "BTC Whale Alert", "size": "xl", "weight": "bold", "color": "#F5FAFE"},
                {"type": "text", "text": f"最大單筆：{wa_max['from']} → {wa_max['to']} {wa_max['amt']} BTC", "size": "sm", "color": "#A3E635"},
                {"type": "text", "text": f"24h共 {wa_total_count} 筆 / {wa_total_amt} BTC", "size": "sm", "color": "#C7D3E6"},
                {"type": "text", "text": f"次大：{wa_2nd['from']} → {wa_2nd['to']} {wa_2nd['amt']} BTC", "size": "sm", "color": "#7dd3fc"}
            ]
        }
    }

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
        "contents": [
            btc_bubble_14d, 
            btc_bubble_hist, 
            eth_bubble_14d, 
            eth_bubble_hist, 
            flex_asset, 
            flex_btc_holder,
            fear_greed_bubble,
            exchange_balance_bubble,
            funding_rate_bubble,
            whale_alert_bubble
        ]
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

def get_pro_plan_carousel():
    bubbles = [
        get_flex_bubble_btc_etf_14d(),
        get_flex_bubble_btc_etf_history(),
        get_flex_bubble_eth_etf_14d(),
        get_flex_bubble_eth_etf_history(),
        get_flex_bubble_top10_assets(),
        get_flex_bubble_btc_holder_distribution(),
        get_flex_bubble_fear_greed(),
        get_flex_bubble_exchange_balance(),
        get_flex_bubble_funding_rate(),
        get_flex_bubble_whale_alert(),
    ]
    return {"type": "carousel", "contents": bubbles[:10]}

def get_elite_carousels():
    bubbles = [
        get_flex_bubble_btc_etf_14d(),
        get_flex_bubble_btc_etf_history(),
        get_flex_bubble_eth_etf_14d(),
        get_flex_bubble_eth_etf_history(),
        get_flex_bubble_top10_assets(),
        get_flex_bubble_btc_holder_distribution(),
        get_flex_bubble_fear_greed(),
        get_flex_bubble_exchange_balance(),
        get_flex_bubble_funding_rate(),
        get_flex_bubble_whale_alert(),
        get_flex_bubble_ahr999(),
        get_flex_bubble_puell_multiple(),
        get_flex_bubble_stock_to_flow(),
        get_flex_bubble_pi_cycle_indicator(),
        get_flex_bubble_profitable_days(),
        get_flex_bubble_borrow_interest_rate(),
        get_flex_bubble_rainbow_chart(),
        get_flex_bubble_stablecoin_marketcap(),
        get_flex_bubble_global_long_short_ratio(),
        get_flex_bubble_grayscale_holdings(),  # 你要的其它專業級
    ]
    # 拆兩組 carousel
    return [
        {"type": "carousel", "contents": bubbles[:10]},
        {"type": "carousel", "contents": bubbles[10:20]}
    ]
