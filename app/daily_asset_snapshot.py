import datetime
from app.fetcher.asset_ranking import fetch_global_asset_top10
from app.pipeline.asset_ranking_df import asset_top10_to_df
from app.db import upsert_global_asset_snapshot

def daily_asset_snapshot():
    today = datetime.date.today().strftime('%Y-%m-%d')
    asset_list = fetch_global_asset_top10()
    df = asset_top10_to_df(asset_list, today)
    upsert_global_asset_snapshot(df)
    print("今日資產市值快照已寫入 Supabase！")
    print(df)

if __name__ == "__main__":
    daily_asset_snapshot()
