from apscheduler.schedulers.blocking import BlockingScheduler
from app.fetcher.marketcap import fetch_global_assets
from app.fetcher.farside import fetch_farside_flows
from app.pipeline.process import process_and_plot
from app.push.line import push_daily_summary

def start_scheduler():
    scheduler = BlockingScheduler(timezone="Asia/Taipei")

    scheduler.add_job(fetch_global_assets, 'cron', hour=18, minute=10, id="fetch_assets")
    scheduler.add_job(fetch_farside_flows, 'cron', hour=18, minute=15, id="fetch_etf")
    scheduler.add_job(process_and_plot, 'cron', hour=18, minute=20, id="process_and_plot")
    scheduler.add_job(push_daily_summary, 'cron', hour=18, minute=30, id="push_summary")

    print("Scheduler started.")
    scheduler.start()
