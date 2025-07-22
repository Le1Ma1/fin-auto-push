import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from app.daily_asset_snapshot import daily_asset_snapshot

# 匯入你的 job function
from app.fetch_etf_daily import fetch_and_save as fetch_etf_daily   # 只拉最近幾天
from app.auto_daily_push import daily_etf_tplus1_push               # 推播
from app.auto_push_asset_competition import main as push_asset_competition

def fetch_all_data():
    fetch_etf_daily("BTC", days=5)
    fetch_etf_daily("ETH", days=5)
    daily_asset_snapshot()
    # 可擴充更多 Job

def push_all_reports():
    daily_etf_tplus1_push("BTC")
    daily_etf_tplus1_push("ETH")
    push_asset_competition()

def main():
    sched = BlockingScheduler(timezone="Asia/Taipei")

    # 13:59 抓取資料
    sched.add_job(fetch_all_data, CronTrigger(hour=13, minute=59))
    # 14:00 推播
    sched.add_job(push_all_reports, CronTrigger(hour=14, minute=0))

    print("🔔 Scheduler started, press Ctrl+C to quit")
    sched.start()

if __name__ == "__main__":
    main()
