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

def fetch_lost_supply_coinglass_utxo_selenium():
    url = "https://www.coinglass.com/zh-TW/pro/i/utxo"
    options = Options()
    tmp_dir = tempfile.mkdtemp()
    options.add_argument("--headless=new")
    options.add_argument(f"--user-data-dir={tmp_dir}")
    options.add_argument("--incognito")
    driver = webdriver.Chrome(options=options)
    try:
        print("[DEBUG] 打開 Coinglass UTXO 頁面...")
        driver.get(url)
        time.sleep(7)
        print("[DEBUG] 頁面加載完畢，開始定位圖表...")

        driver.save_screenshot("utxo_debug.png")
        with open("utxo_page_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # 找到圖表區，模擬滑鼠到最右側
        chart = driver.find_element(By.CLASS_NAME, "chartjs-render-monitor")
        width = chart.size['width']
        height = chart.size['height']
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(chart, width-20, height//2).perform()
        time.sleep(2)

        # 讀取 tooltip 內容
        tooltip = driver.find_element(By.CLASS_NAME, "echarts-tooltip")
        tooltip_text = tooltip.text
        print("[DEBUG] Tooltip:", tooltip_text)

        # 用正則抓 5y~、7y~、10y~ 對應數字
        lost_total = 0
        for k in ["5y~", "7y~", "10y~"]:
            match = re.search(rf"{k}\s*([\d,\.]+)", tooltip_text)
            if match:
                val = float(match.group(1).replace(",", ""))
                print(f"[DEBUG] {k}: {val}")
                lost_total += val
        print(f"[DEBUG] Lost Supply (5y~+7y~+10y~): {lost_total}")
        return int(lost_total)
    except Exception as e:
        print("[ERROR] Selenium 解析失敗:", e)
        import traceback
        print(traceback.format_exc())
        return 0
    finally:
        driver.quit()

import requests
from bs4 import BeautifulSoup
import re

def fetch_miner_balance_coinank():
    url = "https://coinank.com/zh-tw/btcChainDate/btcMinerBalance"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text()
    # 用正則抓 legend 最新一筆數字（一般會有「餘額」或「BTC」等字樣）
    match = re.search(r"餘額[\s:：]*([\d,]+\.?\d*)", text)
    if match:
        value = float(match.group(1).replace(",", ""))
        print(f"[DEBUG] CoinAnk Miner Balance: {value}")
        return int(value)
    # 或直接抓最大數字
    numbers = [float(m.replace(",","")) for m in re.findall(r"([\d,]+\.\d+)", text)]
    if numbers:
        val = int(max(numbers))
        print(f"[DEBUG] CoinAnk Miner Balance (max): {val}")
        return val
    print("[ERROR] 無法穩定抓到 Miner Balance 數字")
    return 0

def fetch_btc_holder_distribution():
    result = []  # << 這一行必加!
    # 1. 已遺失（假資料/待補真實爬蟲）
    lost_btc = fetch_lost_supply_coinglass_utxo_selenium()
    result.append({"category": "已遺失", "btc_count": lost_btc, "percent": None, "source": "Coinglass-UTXO(Selenium)"})
    # 2. 長期持有者
    lth_btc = fetch_longterm_holder_supply_coinglass()
    result.append({"category": "長期持有者", "btc_count": lth_btc, "percent": None, "source": "Coinglass"})
    # 3. 交易所儲備
    exchange_btc = fetch_exchange_reserves_coinglass()
    result.append({"category": "交易所儲備", "btc_count": exchange_btc, "percent": None, "source": "Coinglass"})
    # 4. 礦工持有（假資料/待補）
    miner_btc = fetch_miner_balance_coinank()
    result.append({"category": "礦工持有", "btc_count": miner_btc, "percent": None, "source": "CoinAnk"})
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
