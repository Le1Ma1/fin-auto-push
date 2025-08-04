import requests
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def fetch_and_save_whale_alert(days=1):
    url = 'https://open-api-v4.coinglass.com/api/hyperliquid/whale-alert?symbol=BTC'
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    r = requests.get(url, headers=headers, timeout=10)
    result = r.json()
    data = result.get('data', [])
    today = pd.Timestamp.today().strftime('%Y-%m-%d')
    records = []
    for row in data:
        records.append({
            "date": today,
            "from_address": row.get('fromAddress', row.get('from_address', '')),
            "to_address": row.get('toAddress', row.get('to_address', '')),
            "amount": float(row.get('amount', 0)),
            "tx_time": pd.to_datetime(row.get('timestamp', row.get('tx_time', 0)), unit='ms').strftime("%Y-%m-%d %H:%M:%S"),
        })
    supabase.table("whale_alert").upsert(records).execute()
    print(f"✅ Whale Alert 共 {len(records)} 筆已寫入 Supabase！")

if __name__ == "__main__":
    fetch_and_save_whale_alert()
