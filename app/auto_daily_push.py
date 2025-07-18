from app.db import query_etf_flows_all
from app.plot_chart import plot_etf_bar_chart, plot_etf_history_line_chart
from app.push.push_etf_chart import upload_imgbb
from app.utils import human_unit, etf_flex_table_single_day

def daily_etf_tplus1_push(symbol="BTC"):
    # 1. 查資料
    df_all = query_etf_flows_all(symbol)
    settled_date, df_yesterday = get_latest_settled_date(df_all)
    if settled_date is None:
        print(f"{symbol} 昨日（T-1）ETF 資金流尚未結算完整，暫不推播")
        return
    # 2. 撈近 14 天完整資料
    df_14d = get_recent_14_days_settled(df_all)

    # 3. 畫圖（bubble/bar/line 皆可）
    img_path = plot_etf_bar_chart(df_14d, symbol, days=14)
    img_url = upload_imgbb(img_path)

    # 4. 計算明細（今日ETF資金流/總流量）
    total_today = df_yesterday['flow_usd'].sum()
    etf_today_table = etf_flex_table_single_day(df_yesterday)

    # 5. 自動組推播內容
    push_text = (
        f"{symbol} ETF【昨日（{settled_date}）】完整資金流報告\n"
        f"總淨流入/流出：{human_unit(total_today)}\n"
        "ETF 明細：\n"
    )
    for box in etf_today_table:
        push_text += f"{box['contents'][0]['text']} : {box['contents'][1]['text']}\n"

    print(f"要推播內容：\n{push_text}")
    print(f"圖表網址：{img_url}")
    # 這裡接 LINE Bot、Email、或任意自動推播平台

# 直接在每天台灣時間 14:00 後呼叫
if __name__ == "__main__":
    daily_etf_tplus1_push("BTC")
    daily_etf_tplus1_push("ETH")
