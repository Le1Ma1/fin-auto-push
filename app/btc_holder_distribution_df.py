import pandas as pd

def btc_holder_df_to_db(df: pd.DataFrame):
    """
    資料清理、欄位格式化，可進階補足缺值、自動換算佔比
    """
    df["btc_count"] = pd.to_numeric(df["btc_count"], errors="coerce").fillna(0)
    df["percent"] = pd.to_numeric(df["percent"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df
