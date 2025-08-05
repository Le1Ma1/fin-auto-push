import requests
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
CHUNK_SIZE = 1000

def fetch_and_save_whale_alert(symbol='BTC'):
    """
    自動抓取 Coinglass Hyperliquid Whale Alert 最新異動，落地寫入 Supabase 雲資料庫。
    主鍵去重，支援多幣種。
    """
    url = f'https://open-api-v4.coinglass.com/api/hyperliquid/whale-alert?symbol={symbol}'
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    r = requests.get(url, headers=headers, timeout=10)
    result = r.json()
    data = result.get('data', [])
    today = pd.Timestamp.today().strftime('%Y-%m-%d')
    print("[DEBUG] API data sample:", data[:3])
    records = []
    for row in data:
        records.append({
            "date": today,
            "symbol": row.get('symbol', symbol),
            "user_address": row.get('user', ''),
            "position_size": float(row.get('position_size', 0)),
            "position_action": int(row.get('position_action', 0)),
            "position_value_usd": float(row.get('position_value_usd', 0)),
            "entry_price": float(row.get('entry_price', 0)),
            "liq_price": float(row.get('liq_price', 0)),
            "tx_time": pd.to_datetime(row.get('create_time', 0), unit='ms').strftime("%Y-%m-%d %H:%M:%S"),
        })
    print(f"[LOG] Prepared records: {len(records)}")

    # ---- 主鍵去重：symbol+tx_time+user_address
    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=['symbol', 'tx_time', 'user_address'])
    records = df.to_dict('records')
    print(f"[LOG] Deduped records: {len(records)}")

    # ---- 分批 upsert ----
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i:i+CHUNK_SIZE]
        print(f"[LOG] Upserting chunk {i//CHUNK_SIZE+1} ({len(chunk)} records)")
        resp = supabase.table("whale_alert").upsert(chunk).execute()
        print("[LOG] Upsert chunk response:", resp)
    print(f"[INFO] Whale Alert | {symbol} | 共 {len(records)} 筆已寫入 Supabase！")

if __name__ == "__main__":
    fetch_and_save_whale_alert()
