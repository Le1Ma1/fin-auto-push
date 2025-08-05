import os
import requests
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
CHUNK_SIZE = 1000

def fetch_and_save_funding_rate(
    symbol: str = "BTCUSDT",
    exchange: str = "Binance",
    interval: str = "1d",
    days: int | None = 2000,
) -> None:
    if not COINGLASS_API_KEY:
        raise RuntimeError("⚠️  Missing COINGLASS_API_KEY in environment variables")
    symbol = symbol.strip()
    exchange = exchange.strip()
    url = (
        "https://open-api-v4.coinglass.com/api/futures/funding-rate/history"
        f"?exchange={exchange}&symbol={symbol}&interval={interval}"
    )
    print(f"[DEBUG] API URL: {url}")
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data", [])
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"[FundingRate] Unexpected payload: {payload}")
    if days and len(data) > days:
        data = data[-days:]
    records: list[dict] = []
    for row in data:
        date = pd.to_datetime(row["time"], unit="ms").strftime("%Y-%m-%d")
        records.append(
            {
                "date": date,
                "exchange": exchange,
                "symbol": symbol,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
        )
    print(f"[LOG] Prepared records: {len(records)}")
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i:i+CHUNK_SIZE]
        print(f"[LOG] Upserting chunk {i//CHUNK_SIZE+1} ({len(chunk)} records)")
        resp = supabase.table("funding_rate").upsert(chunk).execute()
        print("[LOG] Upsert chunk response:", resp)
    print(f"✅ FundingRate | {exchange} {symbol} | {len(records)} rows upserted to Supabase")

if __name__ == "__main__":
    fetch_and_save_funding_rate()
