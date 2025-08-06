import pandas as pd
import re

def parse_market_cap_symbol(s):
    if not isinstance(s, str):
        return 0
    s = s.replace("$", "").replace(",", "").strip()
    match = re.match(r'([0-9.]+)\s*([TBM]?)', s)
    if not match:
        return 0
    num, unit = match.groups()
    try:
        num = float(num)
    except Exception:
        return 0
    unit_map = {"T": 1e12, "B": 1e9, "M": 1e6}
    mult = unit_map.get(unit.upper(), 1)
    return num * mult

def asset_top10_to_df(asset_list, date):
    df = pd.DataFrame(asset_list)
    # 這裡的 symbol 就是市值欄位（字串），直接轉成 market_cap_num
    df['market_cap_num'] = df['symbol'].apply(parse_market_cap_symbol)
    df['date'] = date
    return df
