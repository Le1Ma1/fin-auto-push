import requests
from bs4 import BeautifulSoup

def fetch_global_asset_top10():
    url = "https://companiesmarketcap.com/assets-by-market-cap/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    result = []
    for item in soup.select("table tbody tr")[:10]:  # 只抓前10
        cols = item.find_all("td")
        rank = int(cols[0].text.strip())
        name = cols[1].text.strip()
        symbol = cols[2].text.strip()
        market_cap = cols[3].text.strip()
        logo_url = cols[1].find("img")['src'] if cols[1].find("img") else None
        result.append({
            "rank": rank,
            "name": name,
            "symbol": symbol,
            "market_cap": market_cap,
            "logo": logo_url,
        })
    return result