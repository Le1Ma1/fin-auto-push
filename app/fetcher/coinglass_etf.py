import requests
import datetime
import os

def fetch_etf_flow(symbol="BTC", days=10):
    '''
    symbol: 幣種名稱, 如 "BTC", "ETH"
    days: 幾天 (取最近 N 天)
    回傳: Coinglass ETF flow API 的近 N 天原始 json
    '''
    COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")  # 請放在 .env
    assert COINGLASS_API_KEY, "請在 .env 設定 COINGLASS_API_KEY"
    symbol = symbol.lower()

    # 只支援 BTC/ETH
    if symbol == "btc":
        url = "https://open-api-v4.coinglass.com/api/etf/bitcoin/flow-history"
    elif symbol == "eth":
        url = "https://open-api-v4.coinglass.com/api/etf/ethereum/flow-history"
    else:
        raise ValueError(f"不支援的 symbol: {symbol}")

    headers = {
        "accept": "application/json",
        "CG-API-KEY": COINGLASS_API_KEY
    }

    resp = requests.get(url, headers=headers, timeout=20)
    data = resp.json().get("data", [])
    # 按照 timestamp 排序（保證資料正確）
    data = sorted(data, key=lambda x: x['timestamp'])
    # 保留最近 N 天
    if len(data) > days:
        data = data[-days:]
    return {"data": data}
