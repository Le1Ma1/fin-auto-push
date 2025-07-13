import requests
from datetime import datetime
from app.db import upsert_row

def fetch_global_assets():
    url = "https://8marketcap.com/api/v1/assets/rankings"
    resp = requests.get(url)
    assets = resp.json()["data"]

    date = datetime.now().date()
    for asset in assets:
        record = {
            "symbol": asset["symbol"],
            "name": asset["name"],
            "asset_type": asset.get("type", "unknown"),
            "date": str(date),
            "market_cap": float(asset["market_cap_usd"]),
            "rank": int(asset["rank"]),
            "data_json": asset,
        }
        upsert_row("global_assets", record, on_conflict=["symbol", "date"])
    print(f"[{date}] 已儲存全球資產市值排行")
