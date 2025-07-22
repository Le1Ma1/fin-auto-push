import os
from dotenv import load_dotenv
from app.fetcher.coinglass_etf import fetch_etf_flow
from app.pipeline.processor import process_etf_flows_json
from app.db import upsert_etf_flows

load_dotenv()

def fetch_and_save(symbol, days=5):
    json_data = fetch_etf_flow(symbol, days)
    print(f"拉取到 {symbol} 原始 json：", json_data)
    df = process_etf_flows_json(json_data, symbol)
    upsert_etf_flows(df)
    print(f"✅ {symbol} 近{days}日資料已 upsert 到 Supabase")

if __name__ == "__main__":
    fetch_and_save("BTC", days=5)
    fetch_and_save("ETH", days=5)
