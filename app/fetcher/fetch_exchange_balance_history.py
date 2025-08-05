import requests
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
CHUNK_SIZE = 1000

def fetch_and_save_exchange_balance_history():
    url = 'https://open-api-v4.coinglass.com/api/exchange/balance/chart?symbol=BTC'
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    r = requests.get(url, headers=headers, timeout=20)
    result = r.json()
    data = result.get('data', {})
    time_list = data.get('time_list', [])
    data_map = data.get('data_map', {})

    # 檢查資料
    if not time_list or not data_map:
        print("[ERROR] API response format unexpected:", result)
        return

    # 轉換為每天每個交易所一筆紀錄
    records = []
    for exch, balance_list in data_map.items():
        for idx, bal in enumerate(balance_list):
            if bal is None:
                continue  # 跳過無資料
            ts = time_list[idx]
            date = pd.to_datetime(ts, unit='ms').strftime('%Y-%m-%d')
            records.append({
                "date": date,
                "exchange": exch,
                "btc_balance": float(bal),
            })
    print(f"[LOG] Prepared records: {len(records)}")

    # 分批 upsert
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i:i+CHUNK_SIZE]
        print(f"[LOG] Upserting chunk {i//CHUNK_SIZE+1} ({len(chunk)} records)")
        resp = supabase.table("exchange_btc_balance").upsert(chunk).execute()
        print("[LOG] Upsert chunk response:", resp)
    print(f"✅ 交易所 BTC 歷史餘額共 {len(records)} 筆已寫入 Supabase！")

if __name__ == "__main__":
    fetch_and_save_exchange_balance_history()
