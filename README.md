# 金融數據自動化推播與可視覺化

自動抓取全球資產市值排行、ETF 資金流，Supabase 雲端存儲、歷史數據彙整、深色折線圖視覺化，定時推播到 LINE 群組。Docker 化、API 安全、異常監控，開箱即用。

## 部署
1. `cp .env.example .env` 並填寫環境參數
2. `pip install -r requirements.txt`
3. `python main.py`
4. （建議 Docker 化上雲）

## 任務流程
- `fetch_global_assets`：爬取 8marketcap 市值排行
- `fetch_etf_flows`：爬取 farside ETF 淨流向
- `process_and_plot`：數據彙整、生成折線圖、上傳雲端
- `push_daily_summary`：推播摘要＋圖表至 LINE 群組
```
fin-auto-push/
├─ app/
│   ├─ __init__.py
│   ├─ config.py            # 讀取 env 與全局參數
│   ├─ db.py                # Supabase 操作
│   ├─ fetcher/
│   │   ├─ __init__.py
│   │   ├─ marketcap.py     # 8marketcap 抓取
│   │   ├─ farside.py           # farside ETF 抓取
│   ├─ pipeline/
│   │   ├─ __init__.py
│   │   ├─ process.py       # 數據整理與可視化
│   │   ├─ plot.py          # 折線圖生成
│   ├─ push/
│   │   ├─ __init__.py
│   │   ├─ line.py          # LINE OA 推播
│   ├─ scheduler.py         # APScheduler 定時任務
│   ├─ alert.py             # 異常監控/告警
├─ migrations/
│   ├─ create_tables.sql    # 建表 SQL
├─ .env
├─ requirements.txt
├─ Dockerfile
├─ main.py                  # 啟動入口
├─ README.md
```
