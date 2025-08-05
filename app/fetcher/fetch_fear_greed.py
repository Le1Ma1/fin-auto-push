import requests
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

CHUNK_SIZE = 1000

def fetch_and_save_fear_greed(days=2000):
    url = 'https://open-api-v4.coinglass.com/api/index/fear-greed-history'
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    r = requests.get(url, headers=headers, timeout=10)
    result = r.json()
    
    # 這裡要正確取得 data 內容
    data = result.get('data', {})
    data_list = data.get('data_list', [])
    time_list = data.get('time_list', [])
    
    if not data_list or not time_list:
        print("[ERROR] API response format unexpected:", result)
        return

    if days and len(data_list) > days:
        data_list = data_list[-days:]
        time_list = time_list[-days:]
    
    records = []
    for score, ts in zip(data_list, time_list):
        date = pd.to_datetime(ts, unit="ms").strftime('%Y-%m-%d')
        records.append({
            "date": date,
            "score": int(score),  # 關鍵：轉成 int
            # "level": None,
        })

    print(f"[LOG] Prepared records: {len(records)}")
    # 分批 upsert
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i:i+CHUNK_SIZE]
        print("[DEBUG] 即將上傳的 chunk：", chunk[:3])
        resp = supabase.table("fear_greed_index").upsert(chunk, on_conflict="date").execute()
        print("[LOG] Upsert chunk response:", resp)
    print(f"✅ 恐懼貪婪指數共 {len(records)} 筆已寫入 Supabase！")

if __name__ == "__main__":
    fetch_and_save_fear_greed()
