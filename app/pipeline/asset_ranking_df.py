import pandas as pd
import re

def parse_market_cap(market_cap_str):
    unit_map = {"T": 1e12, "B": 1e9, "M": 1e6}
    m = re.match(r"\$?([\d.]+)\s*([TBM])", market_cap_str.replace(",", ""))
    if m:
        num, unit = m.groups()
        return float(num) * unit_map.get(unit, 1)
    return float(market_cap_str.replace("$", "").replace(",", ""))

def asset_top10_to_df(asset_list, date):
    df = pd.DataFrame(asset_list)
    df['market_cap_num'] = df['market_cap'].map(parse_market_cap)
    df['date'] = date
    return df
