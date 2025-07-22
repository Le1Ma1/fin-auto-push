import os
import datetime
import pandas as pd
import math, time
import numpy as np
from dotenv import load_dotenv
from supabase import create_client

# 萬用抓環境變數 function
def env_any(*names):
    for n in names:
        v = os.getenv(n)
        if v: return v
    return None

load_dotenv()

SUPABASE_URL = env_any(
    'SUPABASE_URL', 'supabase_url', 'SUPABASE-URL', 'supabase-url'
)
SUPABASE_KEY = env_any(
    'SUPABASE_KEY', 'supabase_key', 'SUPABASE-KEY', 'supabase-key'
)
LINE_CHANNEL_SECRET = env_any(
    'LINE_CHANNEL_SECRET', 'line_channel_secret', 'LINE-CHANNEL-SECRET', 'line-channel-secret'
)
LINE_CHANNEL_ACCESS_TOKEN = env_any(
    'LINE_CHANNEL_ACCESS_TOKEN', 'line_channel_access_token', 'LINE-CHANNEL-ACCESS-TOKEN', 'line-channel-access-token'
)
LINE_ADMIN_USER_ID = env_any(
    'LINE_ADMIN_USER_ID', 'line_admin_user_id', 'LINE-ADMIN-USER-ID', 'line-admin-user-id'
)
PUSH_GROUP_IDS = env_any(
    'PUSH_GROUP_IDS', 'push_group_ids', 'PUSH-GROUP-IDS', 'push-group-ids'
)
IMGBB_API_KEY = env_any(
    'IMGBB_API_KEY', 'imgbb_api_key', 'IMGBB-API-KEY', 'imgbb-api-key'
)
COINGLASS_API_KEY = env_any(
    'COINGLASS_API_KEY', 'coinglass_api_key', 'COINGLASS-API-KEY', 'coinglass-api-key'
)
TZ = env_any(
    'TZ', 'tz'
)

# Debug
print("[DEBUG] SUPABASE_URL:", SUPABASE_URL)
print("[DEBUG] SUPABASE_KEY:", SUPABASE_KEY[:12], "..." if SUPABASE_KEY else "空值")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def query_etf_flows_all(symbol, table="etf_flows"):
    # 分頁抓取全部歷史資料
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

def query_etf_flows(symbol, days=None, table="etf_flows"):
    q = supabase.table(table).select("*").eq("asset", symbol)
    if days is not None:
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days-1)
        q = q.gte("date", str(start_date))
    q = q.order("date", desc=False).limit(10000)
    resp = q.execute()
    df = pd.DataFrame(resp.data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def upsert_etf_flows(df, table="etf_flows", batch_size=500, retry_times=3):
    allow_cols = ["date", "asset", "etf_ticker", "flow_usd", "price_usd", "total_flow_usd"]
    df = df[allow_cols].dropna(subset=["date", "asset", "etf_ticker"])
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    for col in ["asset", "etf_ticker"]:
        df[col] = df[col].astype(str).fillna("")
    for col in ["flow_usd", "price_usd", "total_flow_usd"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df.drop_duplicates(subset=["date", "asset", "etf_ticker"], keep="last")
    rows = df.to_dict(orient="records")
    total = len(rows)

    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]

        # ========== 逐筆刪除 ==========
        for row in batch:
            for attempt in range(retry_times):
                try:
                    supabase.table(table)\
                        .delete()\
                        .eq("date", row["date"])\
                        .eq("asset", row["asset"])\
                        .eq("etf_ticker", row["etf_ticker"])\
                        .execute()
                    break
                except Exception as e:
                    print(f"Delete error ({row['date']} {row['asset']} {row['etf_ticker']}) (try {attempt+1}): {e}")
                    if attempt < retry_times - 1:
                        time.sleep(2)
                    else:
                        print("Skip delete.")

        # ========== 批次插入 ==========
        for attempt in range(retry_times):
            try:
                supabase.table(table).insert(batch).execute()
                print(f"Batch insert [{i} ~ {i+len(batch)-1}] OK")
                break
            except Exception as e:
                print(f"Batch insert error [{i} ~ {i+len(batch)-1}] (try {attempt+1}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(2)
                else:
                    print("Skip insert batch.")

def upsert_global_asset_snapshot(df, table="global_asset_snapshot", batch_size=20):
    # 只保留合法欄位
    allow_cols = ["date", "rank", "name", "symbol", "market_cap", "market_cap_num", "logo"]
    df = df[allow_cols]
    df = df.drop_duplicates(subset=["date", "rank", "symbol"], keep="last")
    rows = df.to_dict(orient="records")
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        supabase.table(table).upsert(batch).execute()
    print(f"✅ 已 upsert {total} 筆資產市值快照進 {table}")
