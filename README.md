本專案用於**自動化抓取、同步、查詢與推播美國加密貨幣 ETF（如 BTC/ETH）每日資金流資料**，  
並支援透過 LINE Bot 查詢互動，產出走勢圖、明細與統計。  
整合 Coinglass 官方 API、Supabase 雲端資料庫，支援定時同步、Bubble/Bar/Line 圖表自動產生與圖床推播。

```
FIN-AUTO-PUSH/
│
├── .env / .env.test # 環境變數（API KEY, Token, Supabase 參數）
├── requirements.txt # Python 依賴清單
├── scheduler.py # APScheduler 排程主程式，定時全自動抓資料與推播
├── README.md # 專案說明（可插入本結構總覽）
│
├── app/
│ ├── fetcher/ # 資料抓取層（API / 爬蟲）
│ │ ├── asset_ranking.py # 全球資產排行前10名（網站爬蟲）
│ │ ├── coinglass_etf.py # Coinglass API ETF Flow 抓取工具
│ │ ├── daily_asset_snapshot.py # 每日資產市值快照抓取＋寫入
│ │ ├── fetch_etf_daily.py # 近 N 日 ETF Flow（BTC/ETH）
│ │ ├── fetch_etf_history.py # 歷史 ETF Flow（最長 2000 天）
│ │ ├── fetch_exchange_balance.py # 今日交易所 BTC 餘額快照
│ │ ├── fetch_exchange_balance_history.py # 歷史交易所 BTC 餘額（全所全日）
│ │ ├── fetch_fear_greed.py # 恐懼貪婪指數歷史
│ │ ├── fetch_funding_rate.py # Funding Rate 歷史
│ │ ├── fetch_whale_alert.py # Hyperliquid Whale Alert（大戶持倉異動）
│ │ ├── init.py
│ │ └── pycache/
│ │
│ ├── pipeline/ # DataFrame 層：清洗與資料轉換
│ │ ├── asset_ranking_df.py # 資產榜 JSON → DataFrame/標準格式
│ │ ├── processor.py # ETF Flow JSON → 統一 DataFrame
│ │ ├── init.py
│ │ └── pycache/
│ │
│ ├── push/ # 推播/消息組裝（Flex Bubble 等）
│ │ ├── flex_utils.py # Flex Bubble 組裝共用工具
│ │ ├── line_command_handler.py # LINE 指令入口（管理員/推播/補抓）
│ │ ├── push_btc_holder.py # BTC 持幣分布 Bubble 圖組裝
│ │ ├── push_etf_chart.py # ETF Flow/資產快照 Bubble 圖組裝
│ │ ├── push_utils.py # 推播工具（多用戶/群）
│ │ ├── mylog.log # 執行日誌
│ │ ├── init.py
│ │ └── pycache/
│ │
│ ├── btc_holder_distribution.py # 六大類 BTC 持幣分類資料（API/本地聚合）
│ ├── btc_holder_distribution_df.py # 六分類清洗、補齊、落地
│ ├── db.py # Supabase 寫入/查詢/批次 upsert
│ ├── plot_chart.py # 通用繪圖工具
│ ├── plot_chart_btc_holder.py # BTC 六分類圓餅圖繪圖
│ ├── plot_exchange_balance.py # 交易所 BTC 餘額歷史圖
│ ├── plot_fear_greed.py # 恐懼貪婪指數折線圖
│ ├── plot_funding_rate.py # Funding Rate 歷史折線圖
│ ├── plot_whale_alert.py # Whale Alert 持倉異動圖
│ ├── utils.py # 其他工具（公用小工具）
│ └── init.py
│
├── supabase_test.py # Supabase 連線測試
├── test_upload_to_r2.py # Cloudflare R2 圖片上傳測試
├── insert_fake_btc_holder.py # 測試資料生成
├── NotoSansTC-Regular.ttf # 圖表中文字型
└── .gitignore / .github/ / pycache/
```
