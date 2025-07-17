# 金融數據自動化推播與可視覺化

本專案旨在建構一套雲端化、可持續維運的金融數據自動爬取與資料處理系統，並支援資料清洗、標準化與後續分析、推播或自動存儲。架構設計參照現代軟體工程模組化分層原則，強調責任分離與流程一致性，以利未來橫向擴充與個人持續精進。

```
fin-auto-push/                         # 主專案資料夾
│
├─ .env                                # 環境變數設定（API KEY、Supabase 連線資訊）
├─ requirements.txt                    # Python 套件清單
├─ README.md                           # 專案說明檔
│
├─ main.py                             # (可選) 專案進入點，可用於手動全歷史匯入（可刪，已移至 tasks）
│
├─ app/                                # 專案主程式資料夾
│  ├─ __init__.py                      # Python package 初始化檔
│  ├─ config.py                        # Supabase 與 API KEY 設定
│  ├─ db.py                            # 資料庫讀寫（查詢/逐筆 upsert/batch upsert function）
│  ├─ utils.py                         # 工具函數（格式轉換、Flex Table、人性化單位等）
│  ├─ plot_chart.py                    # 畫圖模組 (matplotlib 繪圖與字體設定)
│
│  ├─ fetcher/                         # 對接外部 API 取得原始資料
│  │   ├─ coinglass_etf.py             # fetch_etf_flow（對 Coinglass API 抓 BTC/ETH ETF 歷史資料）
│  │
│  ├─ pipeline/                        # 各種資料清理、轉換
│  │   ├─ processor.py                 # process_etf_flows_json (Coinglass json 轉 DataFrame)
│  │
│  ├─ push/                            # 圖片上傳、LINE 推播等
│  │   ├─ push_etf_chart.py            # upload_imgbb (圖片上傳 imgbb)
│  │   ├─ line_command_handler.py      # FastAPI + LINE Bot 主 webhook 處理
│  │
│  ├─ tasks/                           # 任務腳本 (批次寫入、定時更新)
│  │   ├─ fetch_etf_history.py         # BTC/ETH 全歷史匯入（批次 upsert）
│  └─  ├─ fetch_etf_daily.py           # 每日自動抓取更新
```
