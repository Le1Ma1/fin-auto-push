from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from app.fetcher.daily_asset_snapshot import daily_asset_snapshot
from app.fetcher.fetch_etf_daily import fetch_and_save as fetch_etf_daily
from app.push.push_utils import push_flex_to_targets
from app.push.flex_utils import get_full_flex_carousel 

def fetch_all_data():
    fetch_etf_daily("BTC", days=5)
    fetch_etf_daily("ETH", days=5)
    daily_asset_snapshot()
    # 新增：抓六大類
    df_btc_holder = fetch_btc_holder_distribution()
    df_btc_holder = btc_holder_df_to_db(df_btc_holder)
    upsert_btc_holder_distribution(df_btc_holder)

def push_all_reports():
    # 這裡直接產生五合一 carousel 並推播多用戶
    flex_carousel = get_full_flex_carousel()
    push_flex_to_targets(flex_carousel)

def main():
    sched = BlockingScheduler(timezone="Asia/Taipei")

    # 13:50 抓取資料    
    print('爬取數據中')
    sched.add_job(fetch_all_data, CronTrigger(hour=13, minute=50))
    print('爬取完成')
    # 14:00 推播
    sched.add_job(push_all_reports, CronTrigger(hour=14, minute=00))
    print('推播完成')

    print("🔔 Scheduler started, press Ctrl+C to quit")
    sched.start()

if __name__ == "__main__":
    main()
