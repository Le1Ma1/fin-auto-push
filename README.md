# 金融數據自動化推播與可視覺化

本專案旨在建構一套雲端化、可持續維運的金融數據自動爬取與資料處理系統，並支援資料清洗、標準化與後續分析、推播或自動存儲。架構設計參照現代軟體工程模組化分層原則，強調責任分離與流程一致性，以利未來橫向擴充與個人持續精進。

```
fin-auto-push/
│
├── app/
│   ├── db.py                      # Supabase 查詢/寫入 ETF 資料
│   ├── utils.py                   # 單位轉換、人性化數字、Flex 明細組裝
│   ├── plot_chart.py              # ETF bar/line 圖表產生
│   ├── config.py                  # API 金鑰、Supabase client 設定
│   ├── fetcher/
│   │   └── coinglass_etf.py       # 拉 coinglass API，ETF 原始數據
│   ├── pipeline/
│   │   └── processor.py           # API 回傳 JSON 轉 DataFrame
│   ├── push/
│   │   ├── line_command_handler.py # FastAPI + LINE webhook 主控（業務邏輯/組圖表/Flex）
│   │   └── push_etf_chart.py      # 圖片上傳 imgbb 圖床
│   └── tasks/
│       └── fetch_etf_daily.py     # 自動拉取近 10 天資料 upsert（定時自動化/cron 專用）
│
├── requirements.txt               # Python 套件需求
├── .env                           # API 金鑰、環境變數
├── README.md                      # 專案說明文件
```
