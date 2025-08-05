import requests
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
CHUNK_SIZE = 1000

def fetch_and_save_exchange_balance(days=1):
    url = 'https://open-api-v4.coinglass.com/api/exchange/balance/list?symbol=BTC'
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    r = requests.get(url, headers=headers, timeout=10)
    result = r.json()
    data = result.get('data', [])
    today = pd.Timestamp.today().strftime('%Y-%m-%d')
    records = []
    for row in data:
        records.append({
            "date": today,
            "exchange": row['exchangeName'] if 'exchangeName' in row else row.get('exchange_name', ''),
            "btc_balance": float(row['totalBalance']) if 'totalBalance' in row else float(row.get('total_balance', 0)),
        })
    print(f"[LOG] Prepared records: {len(records)}")
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i:i+CHUNK_SIZE]
        print(f"[LOG] Upserting chunk {i//CHUNK_SIZE+1} ({len(chunk)} records)")
        resp = supabase.table("exchange_btc_balance").upsert(chunk).execute()
        print("[LOG] Upsert chunk response:", resp)
    print(f"✅ 交易所 BTC 餘額共 {len(records)} 筆已寫入 Supabase！")

if __name__ == "__main__":
    fetch_and_save_exchange_balance()
