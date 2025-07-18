from dotenv import load_dotenv
import os
from app.fetcher.coinglass_etf import fetch_etf_flow
from app.pipeline.processor import process_etf_flows_json
from app.db import upsert_etf_flows

load_dotenv()

def fetch_and_save_history(symbol="BTC", days=2000):
    json_data = fetch_etf_flow(symbol, days)
    if not json_data or not json_data.get("data"):
        print(f"❌ 無法取得 {symbol} ETF 歷史數據")
        return
    df = process_etf_flows_json(json_data, symbol)
    upsert_etf_flows(df)
    print(f"✅ {symbol} 歷史 {len(df)} 筆資料 upsert 完成")

if __name__ == "__main__":
    fetch_and_save_history("BTC", days=2000)
    fetch_and_save_history("ETH", days=2000)
