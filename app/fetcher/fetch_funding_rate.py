import os
import requests
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

# ------------------------------------------------------------
#  Coinglass Funding‑Rate OHLC → Supabase
# ------------------------------------------------------------
#  * Endpoint: /api/futures/fundingRate/ohlc-history
#  * Default: Binance BTCUSDT 1‑Day interval (≈ 8‑hour composite)
#  * Upserts to table `funding_rate` with primary key (date, exchange, symbol)
# ------------------------------------------------------------

load_dotenv()
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_and_save_funding_rate(
    symbol: str = "BTCUSDT",
    exchange: str = "Binance",
    interval: str = "1d",
    days: int | None = 2000,
) -> None:
    """Pull funding‑rate OHLC history and upsert to Supabase."""

    if not COINGLASS_API_KEY:
        raise RuntimeError("⚠️  Missing COINGLASS_API_KEY in environment variables")

    url = (
        "https://open-api-v4.coinglass.com/api/futures/fundingRate/ohlc-history"
        f"?exchangeName={exchange}&symbol={symbol}&interval={interval}"
    )
    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    resp = requests.get(url, headers=headers, timeout=20)

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"[FundingRate] HTTP {resp.status_code}: {e}") from None

    payload = resp.json()
    data = payload.get("data", [])
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"[FundingRate] Unexpected payload: {payload}")

    # Limit rows for safety (Coinglass caps at 2 000 anyway)
    if days and len(data) > days:
        data = data[-days:]

    records: list[dict] = []
    for row in data:
        # API uses millisecond timestamps
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

    supabase.table("funding_rate").upsert(records).execute()
    print(
        f"✅ FundingRate | {exchange} {symbol} | {len(records)} rows upserted to Supabase"
    )


if __name__ == "__main__":
    # Full‑history sync for the default pair
    fetch_and_save_funding_rate()
