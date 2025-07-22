本專案用於**自動化抓取、同步、查詢與推播美國加密貨幣 ETF（如 BTC/ETH）每日資金流資料**，  
並支援透過 LINE Bot 查詢互動，產出走勢圖、明細與統計。  
整合 Coinglass 官方 API、Supabase 雲端資料庫，支援定時同步、Bubble/Bar/Line 圖表自動產生與圖床推播。

```
fin-auto-push/
├── .env                       # 各種金鑰、LINE帳號、推播ID、API Key 設定
├── .gitignore                 # Git 版控排除
├── NotoSansTC-Regular.ttf     # 中文字型
├── README.md                  # 專案說明
├── requirements.txt           # Python 套件需求
├── Coinglass 對接文檔.txt    # Coinglass API 使用與測試說明
└── app/
    ├── __init__.py
    ├── db.py                  # 與 Supabase 互動（查、寫、upsert）
    ├── plot_chart.py          # 產生所有 bar/line/橫條圖（matplotlib）
    ├── scheduler.py           # APScheduler 任務排程（抓資料/推播）
    ├── utils.py               # 單位、ETF Flex表格、日期判斷等共用
    ├── fetcher/               # ETF/資產榜 API 爬蟲（抓資料）
    │   ├── __init__.py
    │   ├── asset_ranking.py
    │   ├── coinglass_etf.py
    │   ├── daily_asset_snapshot.py
    │   ├── fetch_etf_daily.py
    │   ├── fetch_etf_history.py
    ├── pipeline/              # DataFrame/欄位處理
    │   ├── __init__.py
    │   ├── asset_ranking_df.py
    │   ├── processor.py
    └── push/                  # 所有推播/訊息相關工具
        ├── __init__.py
        ├── flex_utils.py      # 組合五合一 Flex Bubble（Carousel）
        ├── line_command_handler.py # FastAPI Webhook，支援 SECRET 管理指令
        ├── push_etf_chart.py  # imgbb 圖片上傳
        └── push_utils.py      # 多對象推播（LINE Bot 多群/用戶自動推播）
```
