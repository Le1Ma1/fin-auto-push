import requests, datetime, logging, os
import pandas as pd
from bs4 import BeautifulSoup

COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")

def fetch_coinglass_etf_btc_balance():
    # Coinglass API: Bitcoin ETF List
    url = "https://open-api-v4.coinglass.com/api/etf/bitcoin/list"
    headers = {
        "accept": "application/json",
        "CG-API-KEY": COINGLASS_API_KEY
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        data = resp.json().get("data", [])
        total_btc = 0
        for etf in data:
            asset_details = etf.get("asset_details", {})
            total_btc += float(asset_details.get("btc_holding", 0))
        logging.info(f"[ETF/Institutional] Coinglass 全ETF持有BTC總量: {total_btc}")
        return int(total_btc)
    except Exception as e:
        logging.error(f"[ETF/Institutional] 取得失敗: {e}")
        return 0

def fetch_coinglass_exchange_btc():
    # Coinglass Exchange Reserves BTC
    url = "https://open-api-v4.coinglass.com/api/exchange/bitcoin/reserves"
    headers = {
        "accept": "application/json",
        "CG-API-KEY": "你的Coinglass API Key"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        data = resp.json().get("data", [])
        total_btc = sum(float(d.get("btc", 0)) for d in data)
        logging.info(f"[Speculative/交易所] Coinglass 交易所BTC總量: {total_btc}")
        return int(total_btc)
    except Exception as e:
        logging.error(f"[Speculative/交易所] 取得失敗: {e}")
        return 0

def fetch_unmined_blockchaininfo():
    try:
        resp = requests.get("https://api.blockchair.com/bitcoin/stats")
        stats = resp.json().get("data", {})
        issued = stats.get("circulation", 0)
        max_supply = 21000000
        unmined = max_supply - float(issued)/1e8  # blockchair circulation 單位為 satoshi
        logging.info(f"[未開採] 總量: {max_supply} 已開採: {float(issued)/1e8} 未開採: {unmined}")
        return unmined
    except Exception as e:
        logging.error(f"[未開採] 取得失敗: {e}")
        return 0

def fetch_etf_holdings_bitcointreasuries():
    url = "https://www.bitcointreasuries.net/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        # 用正則找到 <script id="__NEXT_DATA__">...</script>
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text, re.DOTALL)
        if not match:
            logging.error("沒找到 __NEXT_DATA__ script，網頁結構可能變動！")
            return 0
        json_data = json.loads(match.group(1))
        treasuries = json_data['props']['pageProps']['treasuries']
        total_btc = 0
        for item in treasuries:
            btc = float(item.get("btcBalance", 0))
            total_btc += btc
        logging.info(f"[ETF/機構/主權基金] bitcointreasuries.net 全球持有BTC: {total_btc}")
        return int(total_btc)
    except Exception as e:
        logging.error(f"[ETF/機構/主權基金] 取得失敗: {e}")
        return 0

# 測試
if __name__ == "__main__":
    print(fetch_etf_holdings_bitcointreasuries())

def fetch_btc_holder_distribution():
    today = datetime.date.today().strftime("%Y-%m-%d")
    result = []

    # 1. 已遺失（後續再補）
    lost_btc = 3050000
    result.append({"category": "已遺失", "btc_count": lost_btc, "percent": None, "source": "Glassnode"})

    # 2. 長期持有者（後續再補）
    long_term_btc = 14800000
    result.append({"category": "長期持有者", "btc_count": long_term_btc, "percent": None, "source": "Glassnode"})

    # 3. 交易所儲備（後續再補）
    speculative_btc = 1700000
    result.append({"category": "交易所儲備", "btc_count": speculative_btc, "percent": None, "source": "CryptoQuant"})

    # 4. 礦工持有（後續再補）
    miners_btc = 1500000
    result.append({"category": "礦工持有", "btc_count": miners_btc, "percent": None, "source": "CryptoQuant"})

    # 5. ETF/機構/中央銀行
    etf_btc = fetch_etf_holdings_bitcointreasuries()
    result.append({"category": "ETF/機構", "btc_count": etf_btc, "percent": None, "source": "bitcointreasuries.net"})
    # 中央銀行直接歸屬於 ETF/機構總和，可細分來源

    # 6. 未開採
    unmined_btc = fetch_unmined_blockchaininfo()
    result.append({"category": "未開採", "btc_count": unmined_btc, "percent": None, "source": "blockchair.com"})

    # 7. 中央銀行/主權基金 (可再細分來源)
    # 目前可細分薩爾瓦多等政府持有，之後補齊
    result.append({"category": "中央銀行／主權基金", "btc_count": 0, "percent": None, "source": "bitcointreasuries.net"})

    # 計算總量與百分比
    total = sum(x["btc_count"] for x in result)
    for x in result:
        x["percent"] = round(x["btc_count"] / total * 100, 2) if total else None
        x["date"] = today

    df = pd.DataFrame(result)
    return df[["date", "category", "btc_count", "percent", "source"]]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = fetch_btc_holder_distribution()
    print(df)
