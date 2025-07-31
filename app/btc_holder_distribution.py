import requests, os, logging, datetime, time, traceback, tempfile
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

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

def fetch_longterm_holder_supply_coinglass():
    url = "https://open-api-v4.coinglass.com/api/index/bitcoin-long-term-holder-supply"
    headers = {
        "accept": "application/json",
        "CG-API-KEY": os.getenv("COINGLASS_API_KEY")
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        result = resp.json()
        data = result.get("data", [])
        if not data:
            logging.error(f"[長期持有者] Coinglass 沒有 data")
            return 0
        latest = data[-1]
        lth_btc = int(latest.get('long_term_holder_supply', 0))
        logging.info(f"[長期持有者] Coinglass LTH Supply: {lth_btc}")
        return lth_btc
    except Exception as e:
        logging.error(f"[長期持有者] Coinglass 取得失敗: {e}")
        return 0

def fetch_unmined_supply_blockchair():
    url = "https://api.blockchair.com/bitcoin/stats"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()['data']
        # circulation 單位是 satoshi（1 BTC = 1e8 sat）
        circulation_btc = float(data['circulation']) / 1e8
        unmined = 21000000 - circulation_btc
        print(f"[DEBUG] 已開採：{circulation_btc:.2f} BTC，未開採：{unmined:.2f} BTC")
        return int(unmined)
    except Exception as e:
        print("[ERROR] 未開採 取得失敗:", e)
        return 0

def fetch_btc_holder_distribution():
    result = []

    # 五大類直接抓
    lth_btc = fetch_longterm_holder_supply_coinglass()
    exchange_btc = fetch_exchange_reserves_coinglass()
    etf_btc = fetch_etf_holdings_coinglass()
    unmined_btc = fetch_unmined_supply_blockchair()
    central_btc = 0  # 中央銀行

    # 計算其他類
    major_sum = lth_btc + exchange_btc + etf_btc + unmined_btc + central_btc
    other_btc = 21000000 - major_sum

    # 1. 長期持有者
    result.append({
        "category": "長期持有者",
        "btc_count": lth_btc,
        "percent": None,
        "source": "Coinglass"
    })
    # 2. 交易所儲備
    result.append({
        "category": "交易所儲備",
        "btc_count": exchange_btc,
        "percent": None,
        "source": "Coinglass"
    })
    # 3. ETF/機構
    result.append({
        "category": "ETF/機構",
        "btc_count": etf_btc,
        "percent": None,
        "source": "Coinglass"
    })
    # 4. 未開採
    result.append({
        "category": "未開採",
        "btc_count": unmined_btc,
        "percent": None,
        "source": "blockchair.com"
    })
    # 5. 中央銀行／主權基金
    result.append({
        "category": "中央銀行／主權基金",
        "btc_count": central_btc,
        "percent": None,
        "source": "預留"
    })
    # 6. 其他（包含已遺失、礦工持有）
    result.append({
        "category": "其他",
        "btc_count": other_btc,
        "percent": None,
        "source": "自動計算：2100萬 - 其它所有類"
    })

    # 保證總和 2100萬
    total = sum(x["btc_count"] for x in result)
    for x in result:
        x["percent"] = round(x["btc_count"] / total * 100, 2) if total else None
        x["date"] = datetime.date.today().strftime("%Y-%m-%d")

    df = pd.DataFrame(result)
    print(f"[DEBUG] 總和：{total} BTC")  # 可印出 debug
    return df[["date", "category", "btc_count", "percent", "source"]]
