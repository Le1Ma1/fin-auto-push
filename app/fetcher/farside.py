import pandas as pd
from io import StringIO

def fetch_farside_flows(html_path="btc.html"):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    df = pd.read_html(StringIO(html), header=1)[0]
    df = df.rename(columns={"Unnamed: 0": "date", "Unnamed: 12": "total"})
    df = df[df["date"].notnull()]
    df = df[df["date"].str.contains(r"\d{2} \w{3} 20", na=False)]
    df = df.reset_index(drop=True)
    # 將所有金額欄位批次轉 float（含負數處理）
    def parse_num(val):
        val = str(val).replace("(", "-").replace(")", "")
        try:
            return float(val)
        except:
            return 0.0
    for col in df.columns[1:]:
        df[col] = df[col].apply(parse_num)
    return df
