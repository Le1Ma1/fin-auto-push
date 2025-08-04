import requests
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def fetch_and_save_fear_greed(days=2000):
    url = 'https://open-api-v4.coinglass.com/api/index/fear-greed-history'
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    r = requests.get(url, headers=headers, timeout=10)
    result = r.json()
    data = result.get('data', [])
    # 有時會是 dict (有 'history')
    if isinstance(data, dict) and 'history' in data:
        data = data['history']
    if not isinstance(data, list):
        print("[ERROR] data is not list:", data)
        return
    if days and len(data) > days:
        data = data[-days:]
    records = []
    for row in data:
        date = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
        records.append({
            "date": date,
            "score": row.get("score"),
            "level": row.get("level"),
        })
    supabase.table("fear_greed_index").upsert(records).execute()
    print(f"✅ 恐懼貪婪指數共 {len(records)} 筆已寫入 Supabase！")

if __name__ == "__main__":
    fetch_and_save_fear_greed()
