import datetime
import pandas as pd
import math, time
from app.config import supabase

def query_etf_flows_all(symbol, table="etf_flows"):
    # 分頁抓取 supabase 資料，確保抓取全部歷史資料
    # 示意：可根據 Supabase 預設分頁大小調整
    limit = 1000
    offset = 0
    all_data = []

    while True:
        resp = supabase.table(table).select("*").eq("asset", symbol).order("date", desc=False).limit(limit).offset(offset).execute()
        data = resp.data
        if not data:
            break
        all_data.extend(data)
        offset += limit

    df = pd.DataFrame(all_data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def upsert_etf_flows(df, table="etf_flows", batch_size=500, retry_times=3):
    allow_cols = ["date", "asset", "etf_ticker", "flow_usd", "price_usd", "total_flow_usd"]
    df = df[allow_cols].dropna(subset=["date", "asset", "etf_ticker"])
    rows = df.to_dict(orient="records")
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        # 轉 NaN/NaT 為 None
        for row in batch:
            for k, v in row.items():
                if pd.isna(v) or (isinstance(v, float) and math.isnan(v)):
                    row[k] = None
        for attempt in range(retry_times):
            try:
                supabase.table(table).upsert(batch).execute()
                print(f"Upsert [{i} ~ {i+len(batch)-1}] OK")
                break
            except Exception as e:
                print(f"Batch upsert error [{i} ~ {i+len(batch)-1}] (try {attempt+1}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(3)  # 等 3 秒後重試
                else:
                    print("Skip this batch.")

def query_etf_flows(symbol, days=None, table="etf_flows"):
    q = supabase.table(table).select("*").eq("asset", symbol)
    if days is not None:
        import datetime
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days-1)
        q = q.gte("date", str(start_date))
    q = q.order("date", desc=False).limit(10000)
    resp = q.execute()
    df = pd.DataFrame(resp.data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

