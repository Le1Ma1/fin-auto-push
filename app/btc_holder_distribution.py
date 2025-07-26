import requests, datetime, logging, os
import pandas as pd

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

def fetch_unmined_supply():
    # blockchain.info API
    try:
        resp = requests.get("https://blockchain.info/q/unminedblocks")
        unmined = int(resp.text)
        block_reward = 3.125  # 如遇減半需更新
        est_unmined = unmined * block_reward
        logging.info(f"[Unmined Supply] 未開採BTC: {est_unmined} (區塊數: {unmined})")
        return est_unmined
    except Exception as e:
        logging.error(f"[Unmined Supply] 取得失敗: {e}")
        return 0

def fetch_btc_holder_distribution():
    today = datetime.date.today().strftime("%Y-%m-%d")
    result = []

    # --- 以下真 API 可用則用，無資料或失敗時設 0 ---
    etf_btc = 0           # ETF/機構
    speculative_btc = 0   # 交易所儲備
    unmined_btc = 0       # 未開採

    # 其它用假資料（如上一步測試）
    long_term_btc = 14800000
    lost_btc = 3050000
    miners_btc = 1500000

    # 1. 已遺失
    result.append({"category": "已遺失", "btc_count": lost_btc, "percent": None, "source": "IntoTheBlock"})
    # 2. 長期持有者
    result.append({"category": "長期持有者", "btc_count": long_term_btc, "percent": None, "source": "CryptoQuant"})
    # 3. 交易所儲備
    result.append({"category": "交易所儲備", "btc_count": speculative_btc, "percent": None, "source": "Coinglass"})
    # 4. 礦工持有
    result.append({"category": "礦工持有", "btc_count": miners_btc, "percent": None, "source": "BTC.com"})
    # 5. ETF/機構
    result.append({"category": "ETF/機構", "btc_count": etf_btc, "percent": None, "source": "Coinglass"})
    # 6. 未開採
    result.append({"category": "未開採", "btc_count": unmined_btc, "percent": None, "source": "blockchain.info"})
    # 7. 中央銀行／主權基金（前瞻性空欄）
    result.append({"category": "中央銀行／主權基金", "btc_count": 0, "percent": None, "source": "暫無"})

    # 計算總量與百分比
    total = sum(x["btc_count"] for x in result)
    for x in result:
        x["percent"] = round(x["btc_count"] / total * 100, 2) if total else None
        x["date"] = today

    df = pd.DataFrame(result)
    logging.info(f"[BTC HOLDER] 七分類分布: \n{df}")
    return df[["date", "category", "btc_count", "percent", "source"]]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = fetch_btc_holder_distribution()
    print(df)
