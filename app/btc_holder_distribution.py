import requests, os, logging, datetime
import pandas as pd

def fetch_etf_holdings_coinglass():
    url = "https://open-api-v4.coinglass.com/api/etf/bitcoin/list"
    headers = {
        "accept": "application/json",
        "CG-API-KEY": os.getenv("COINGLASS_API_KEY")
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        data = resp.json().get("data", [])
        total_btc = 0
        for etf in data:
            asset_details = etf.get("asset_details", {})
            # 正確欄位為 holding_quantity
            holding = float(asset_details.get("holding_quantity", 0))
            total_btc += holding
        logging.info(f"[ETF/機構] Coinglass ETF持有BTC總量: {total_btc}")
        return int(total_btc)
    except Exception as e:
        logging.error(f"[ETF/機構] 取得失敗: {e}")
        return 0

def fetch_exchange_reserves_coinglass():
    url = "https://open-api-v4.coinglass.com/api/exchange/balance/list?symbol=BTC"
    headers = {
        "accept": "application/json",
        "CG-API-KEY": os.getenv("COINGLASS_API_KEY")
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        data = resp.json().get("data", [])
        total_btc = sum(float(ex['total_balance']) for ex in data if ex.get('total_balance'))
        logging.info(f"[交易所儲備] Coinglass API BTC 總量: {total_btc}")
        return int(total_btc)
    except Exception as e:
        logging.error(f"[交易所儲備] Coinglass 取得失敗: {e}")
        return 0

def fetch_btc_holder_distribution():
    result = []  # << 這一行必加!
    # 1. 已遺失（假資料/待補真實爬蟲）
    lost_btc = 3050000
    result.append({"category": "已遺失", "btc_count": lost_btc, "percent": None, "source": "Glassnode"})
    # 2. 長期持有者（假資料/待補）
    long_term_btc = 14800000
    result.append({"category": "長期持有者", "btc_count": long_term_btc, "percent": None, "source": "Glassnode"})
    # 3. 交易所儲備（假資料/待補）
    exchange_btc = fetch_exchange_reserves_coinglass()
    result.append({"category": "交易所儲備", "btc_count": exchange_btc, "percent": None, "source": "Coinglass"})
    # 4. 礦工持有（假資料/待補）
    miners_btc = 1500000
    result.append({"category": "礦工持有", "btc_count": miners_btc, "percent": None, "source": "CryptoQuant"})
    # 5. ETF/機構
    etf_btc = fetch_etf_holdings_coinglass()
    result.append({"category": "ETF/機構", "btc_count": etf_btc, "percent": None, "source": "Coinglass"})
    # 6. 未開採（假資料/待補）
    unmined_btc = 1100000
    result.append({"category": "未開採", "btc_count": unmined_btc, "percent": None, "source": "blockchair.com"})
    # 7. 中央銀行／主權基金
    result.append({"category": "中央銀行／主權基金", "btc_count": 0, "percent": None, "source": "Coinglass"})

    # 加入日期與計算百分比
    total = sum(x["btc_count"] for x in result)
    for x in result:
        x["percent"] = round(x["btc_count"] / total * 100, 2) if total else None
        x["date"] = datetime.date.today().strftime("%Y-%m-%d")

    df = pd.DataFrame(result)
    return df[["date", "category", "btc_count", "percent", "source"]]
