本專案用於**自動化抓取、同步、查詢與推播美國加密貨幣 ETF（如 BTC/ETH）每日資金流資料**，  
並支援透過 LINE Bot 查詢互動，產出走勢圖、明細與統計。  
整合 Coinglass 官方 API、Supabase 雲端資料庫，支援定時同步、Bubble/Bar/Line 圖表自動產生與圖床推播。

```
fin-auto-push/
│
├── README.md                   # 專案說明、功能與部署維護指南
├── .env                        # API Key、環境變數（敏感資訊不進版控）
│
├── app/                        # 主程式碼目錄，邏輯模組化
│   │
│   ├── db.py                   # Supabase 資料庫存取與 CRUD 操作
│   │   └─ 備註：統一所有讀寫資料庫方法，對 ETF 資金流和全球資產市值榜快照表做 upsert/query
│   │
│   ├── utils.py                # 工具函式（格式化單位、日期、表格等）
│   │   └─ 備註：人性化單位換算、市值解析、表格產生、補日期資料等
│   │
│   ├── plot_chart.py           # 圖表產生（Bar/Line/Bubble）
│   │   └─ 備註：ETF/BTC/ETH 資金流、資產市值榜橫向長條圖等自動產生與美化
│   │
│   ├── fetcher/                # 外部 API/資料抓取
│   │   ├── coinglass_etf.py    # Coinglass ETF 流資料 API 拉取
│   │   │   └─ 備註：根據幣別（BTC/ETH）抓取對應天數資料，回傳原始 JSON
│   │
│   ├── pipeline/               # 資料清洗、欄位轉換、標準化
│   │   ├── processor.py        # ETF flow JSON → DataFrame
│   │   │   └─ 備註：解析 Coinglass JSON 並轉標準結構
│   │   ├── asset_ranking_df.py # Top10榜單轉換 DataFrame
│   │   │   └─ 備註：市值字串解析、榜單排序
│   │
│   ├── push/                   # 推播/互動/圖床
│   │   ├── line_command_handler.py # LINE Bot 查詢/互動主入口
│   │   │   └─ 備註：處理所有文字指令、自動回傳卡片/圖表
│   │   ├── push_etf_chart.py       # 圖片上傳到 imgbb 圖床
│   │   │   └─ 備註：回傳圖片 URL 給 LINE FlexMessage 或外部平台
│   │
│   ├── auto_daily_push.py      # 每日自動 ETF 資金流推播（T+1 報表）
│   │   └─ 備註：定時拉資料→畫圖→自動組推播內容
│   ├── auto_push_asset_competition.py # 每日 Top10 資產市值榜推播
│   │   └─ 備註：定時產生市值榜單與圖卡，一鍵推 LINE
│   ├── fetch_etf_daily.py      # 近幾日 ETF 流水帳同步
│   │   └─ 備註：短週期增量更新，適合每天定時
│   ├── fetch_etf_history.py    # 歷史全量 ETF 流水帳同步
│   │   └─ 備註：首建或資料缺失時一次補齊長週期
│   ├── daily_asset_snapshot.py # 全球資產榜每日快照同步
│   │   └─ 備註：Top10 市值榜全自動入庫
│   └── requirements.txt        # Python 依賴套件清單
│
└── 資料庫結構（Supabase）
    ├── etf_flows               # BTC/ETH ETF 資金流日明細表
    │   └─ 欄位：date, asset, etf_ticker, flow_usd, price_usd, total_flow_usd
    └── global_asset_snapshot   # 全球資產市值 Top10 每日榜快照
        └─ 欄位：date, rank, name, symbol, market_cap, market_cap_num, logo
```
