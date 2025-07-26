import requests, os, logging

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
            total_btc += float(asset_details.get("btc_holding", 0))
        logging.info(f"[ETF/機構] Coinglass ETF持有BTC總量: {total_btc}")
        return int(total_btc)
    except Exception as e:
        logging.error(f"[ETF/機構] 取得失敗: {e}")
        return 0

def fetch_btc_holder_distribution():
    ...
    etf_btc = fetch_etf_holdings_coinglass()
    result.append({"category": "ETF/機構", "btc_count": etf_btc, "percent": None, "source": "Coinglass"})
    ...
