import os
import datetime
import pandas as pd
import time
import numpy as np
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_ADMIN_USER_ID = os.getenv('LINE_ADMIN_USER_ID')
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY')
TZ = os.getenv('TZ')

# Debug
print("[DEBUG] SUPABASE_URL:", SUPABASE_URL)
print("[DEBUG] SUPABASE_KEY:", SUPABASE_KEY[:12], "..." if SUPABASE_KEY else "空值")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# ETF Flows
# -----------------------------
def query_etf_flows_all(symbol, table="etf_flows"):
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

        # 逐筆刪除再插入，確保唯一鍵不衝突
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

        # 批次插入
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

# -----------------------------
# Global Asset Snapshot
# -----------------------------
def upsert_global_asset_snapshot(df, table="global_asset_snapshot", batch_size=20):
    allow_cols = ["date", "rank", "name", "symbol", "market_cap", "market_cap_num", "logo"]
    df = df[allow_cols]
    df = df.drop_duplicates(subset=["date", "rank", "symbol"], keep="last")
    rows = df.to_dict(orient="records")
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        supabase.table(table).upsert(batch).execute()
    print(f"✅ 已 upsert {total} 筆資產市值快照進 {table}")

# -----------------------------
# BTC Holder Distribution
# -----------------------------
def upsert_btc_holder_distribution(df, table="btc_holder_distribution", batch_size=50):
    df = df[["date", "category", "btc_count", "percent", "source"]]
    rows = df.to_dict(orient="records")
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        supabase.table(table).upsert(batch).execute()
    print(f"✅ 已 upsert {total} 筆持幣分布進 {table}")

def query_btc_holder_distribution(days=14, table="btc_holder_distribution"):
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days-1)
    resp = supabase.table(table)\
        .select("*")\
        .gte("date", start.strftime("%Y-%m-%d"))\
        .order("date", desc=False)\
        .execute()
    df = pd.DataFrame(resp.data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# -----------------------------
# Bot Whitelist (新增)
# -----------------------------
def upsert_bot_whitelist(user_id, provider="line", plan_code="pro",
                         tier="basic", period="month", period_months=1,
                         scope=None, order_no=None, period_no=None,
                         access_until=None, status="active"):
    row = {
        "user_id": user_id,
        "provider": provider,
        "plan_code": plan_code,
        "tier": tier,
        "period": period,
        "period_months": period_months,
        "scope": scope or [],
        "order_no": order_no,
        "period_no": period_no,
        "access_until": access_until,
        "status": status,
    }
    supabase.table("bot_whitelist").upsert(row).execute()
    print(f"✅ 已 upsert whitelist user {user_id}")

def remove_bot_whitelist(user_id, reason="manual_remove"):
    supabase.table("bot_whitelist")\
        .update({"status": "removed", "removed_reason": reason})\
        .eq("user_id", user_id).execute()
    print(f"🚫 已移除 whitelist user {user_id}, reason={reason}")

def query_active_whitelist():
    now = datetime.datetime.utcnow().isoformat()
    resp = supabase.table("bot_whitelist")\
        .select("user_id")\
        .eq("status", "active")\
        .gte("access_until", now)\
        .execute()
    return [r["user_id"] for r in resp.data]
