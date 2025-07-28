本專案用於**自動化抓取、同步、查詢與推播美國加密貨幣 ETF（如 BTC/ETH）每日資金流資料**，  
並支援透過 LINE Bot 查詢互動，產出走勢圖、明細與統計。  
整合 Coinglass 官方 API、Supabase 雲端資料庫，支援定時同步、Bubble/Bar/Line 圖表自動產生與圖床推播。

```
FIN-AUTO-PUSH/
├── __pycache__/                      # Python 快取目錄
├── .github/                          # GitHub Actions、Issue 模板等
├── .env                              # 環境變數檔（API Key、LINE Token、Supabase 參數…）
├── .env.test                         # 測試用環境變數
├── .gitignore                        # Git 忽略規則
├── NotoSansTC-Regular.ttf            # 中文字型，用於 matplotlib 圖表
├── README.md                         # 專案說明
├── requirements.txt                  # Python 套件清單
├── scheduler.py                      # APScheduler 排程主程式：定時抓資料 & 推播
└── app/                              # 核心程式碼
    ├── __pycache__/                  # Python 快取
    ├── fetcher/                      # 資料抓取（API or 爬蟲）
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── asset_ranking.py          # 爬取全球資產市值前 10 名
    │   ├── coinglass_etf.py          # Coinglass API：ETF flow 原始 JSON
    │   ├── daily_asset_snapshot.py   # 每日資產榜快照並上傳 Supabase
    │   ├── fetch_etf_daily.py        # 每日近 N 日 BTC/ETH ETF Flow
    │   └── fetch_etf_history.py      # 歷史 ETF Flow 數據（最多 2000 天）
    │
    ├── pipeline/                     # DataFrame 清洗與處理
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── asset_ranking_df.py       # 資產榜 JSON → DataFrame
    │   └── processor.py              # Coinglass JSON → ETF Flow DataFrame
    │
    ├── push/                         # 推播 & Flex message 組裝
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── flex_utils.py             # 組合五合一 Carousel（ETF, 資產榜, BTC六分類）
    │   ├── line_command_handler.py   # FastAPI LINE Webhook + 管理指令
    │   ├── push_btc_holder.py        # BTC 六分類持幣 Flex bubble
    │   ├── push_etf_chart.py         # 圖片上傳 imgbb，回傳 URL
    │   └── push_utils.py             # 多目標 LINE 推播
    │
    ├── __init__.py
    ├── btc_holder_distribution.py    # BTC 六大類持幣爬蟲與組裝邏輯
    ├── btc_holder_distribution_df.py # 將持幣 DataFrame 清洗格式化
    ├── db.py                         # Supabase 資料庫查詢/Upsert/Delete
    ├── plot_chart.py                # ETF & 資產榜 Bar/Line/橫條圖
    ├── plot_chart_btc_holder.py     # BTC 六分類 圓餅圖 & 面積堆疊圖
    └── utils.py                     # 共用工具：單位換算、人類易讀格式、日期判斷
```
