import pandas as pd
from app.db import upsert_btc_holder_distribution

date = "2025-08-02"
data = [
    {"date": date, "category": "長期持有者", "btc_count": 13000000, "percent": 61.9, "source": "手動補齊"},
    {"date": date, "category": "交易所儲備", "btc_count": 2000000, "percent": 9.5, "source": "手動補齊"},
    {"date": date, "category": "ETF/機構", "btc_count": 1000000, "percent": 4.8, "source": "手動補齊"},
    {"date": date, "category": "未開採", "btc_count": 1900000, "percent": 9.0, "source": "手動補齊"},
    {"date": date, "category": "中央銀行／主權基金", "btc_count": 200000, "percent": 1.0, "source": "手動補齊"},
    {"date": date, "category": "其他", "btc_count": 4100000, "percent": 19.5, "source": "手動補齊"},
]
df = pd.DataFrame(data)
upsert_btc_holder_distribution(df)
print("✅ 2025-08-02 假資料已補入")
