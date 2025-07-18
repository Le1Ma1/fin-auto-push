本專案用於**自動化抓取、同步、查詢與推播美國加密貨幣 ETF（如 BTC/ETH）每日資金流資料**，  
並支援透過 LINE Bot 查詢互動，產出走勢圖、明細與統計。  
整合 Coinglass 官方 API、Supabase 雲端資料庫，支援定時同步、Bubble/Bar/Line 圖表自動產生與圖床推播。

```
fin-auto-push/
│
├── app/                           # 專案主程式碼目錄
│   ├── db.py                      # Supabase 資料庫存取與 CRUD 操作
│   ├── utils.py                   # 共用工具、單位/格式/日期/表格等
│   ├── plot_chart.py              # 各式圖表產生（Bar/Line/Bubble）
│   │
│   ├── fetcher/                   # 外部 API 資料抓取
│   │   └── coinglass_etf.py       # Coinglass ETF API 抓取
│   ├── pipeline/                  # 資料清洗、轉換、欄位標準化
│   │   └── processor.py           # API JSON → DataFrame 處理邏輯
│   ├── push/                      # 推播、互動與圖床模組
│   │   ├── line_command_handler.py# LINE Bot 查詢互動主入口
│   │   └── push_etf_chart.py      # 圖表圖片上傳工具（imgbb）
│   │
│   ├── auto_daily_push.py         # 每日自動推播主流程（T+1 報表）
│   ├── fetch_etf_daily.py         # 每日增量拉取與補資料
│   ├── fetch_etf_history.py       # 歷史全量補資料（首次或重建）
│   │
│   └── requirements.txt           # Python 依賴套件清單
│
├── .env                           # API 金鑰、敏感環境變數（不進版控）
└── README.md                      # 專案說明、部署與維護文件
```
