import requests
import datetime
import pandas as pd

def fetch_btc_holder_distribution():
    """
    抓取比特幣持幣分布的六大類：Lost、Long-Term、Speculative、Miners、ETF/Institutional、Unmined
    支援主流開源來源 API 或網頁爬蟲
    """
    # TODO: 實作各來源（此處為假資料，換成你的爬蟲 or API）
    today = datetime.date.today().strftime("%Y-%m-%d")
    categories = [
        {"category": "Lost Supply", "btc_count": 3050000, "percent": 14.52, "source": "IntoTheBlock"},
        {"category": "Long-Term Holder", "btc_count": 14800000, "percent": 70.48, "source": "CryptoQuant"},
        {"category": "Speculative", "btc_count": 1700000, "percent": 8.1, "source": "Coinglass"},
        {"category": "Miners", "btc_count": 1500000, "percent": 7.14, "source": "BTC.com"},
        {"category": "ETF/Institutional", "btc_count": 1050000, "percent": 5.0, "source": "Coinglass"},
        {"category": "Unmined Supply", "btc_count": 2010000, "percent": 9.57, "source": "blockchain.info"},
    ]
    df = pd.DataFrame(categories)
    df["date"] = today
    cols = ["date", "category", "btc_count", "percent", "source"]
    df = df[cols]
    return df

if __name__ == "__main__":
    print(fetch_btc_holder_distribution())
